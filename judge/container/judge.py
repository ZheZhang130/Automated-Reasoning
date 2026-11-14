"""csc2108 judge: run a stdin/stdout Python submission against one task's tests.

Runs inside the long-lived csc2108-judge container as root (with a reduced
capability set). Submissions run as unprivileged per-slot users and cannot read
the tests. Standard library only.

    judge load --suite NAME             stdin: tar of <task_id>/{NN.in, NN.out, task.json}
    judge info                          print the loaded suite
    judge run --task ID [--time-limit S]
                                        stdin: source code, stdout: one result JSON
    judge selftest                      built-in correctness and isolation checks

Exit codes: 0 when a result was produced (whatever the verdict), 1 for a failed
selftest, 2 when the judge itself failed or the request was invalid.

Comparison follows LiveCodeBench's grade_stdio: strip the whole output and each
line, require equal line counts, and accept a line if it matches exactly or both
sides parse to equal lists of Decimals.
"""
import argparse
import datetime
import fcntl
import hashlib
import json
import os
import resource
import shutil
import signal
import subprocess
import sys
import tarfile
import tempfile
import time
from decimal import Decimal, InvalidOperation
from pathlib import Path

JUDGE_VERSION = "0.2.1"

STATE_DIR = Path("/var/judge")          # tmpfs, root only (mode 0700)
SUITE_DIR = STATE_DIR / "suite"         # loaded tests, root only
SUITE_META = STATE_DIR / "suite.json"
LOCK_DIR = STATE_DIR / "slots"
IO_DIR = STATE_DIR / "io"               # stdout/stderr capture files
SELFTEST_DIR = STATE_DIR / "selftest"
WORK_ROOT = Path("/tmp")                # tmpfs, mode 0711: runners cannot list or create here
SHM_DIR = Path("/dev/shm")

RUNNER_UID_BASE = 2000                  # runner-k has uid/gid 2000 + k (created in the image)
MAX_SLOTS = 16
SLOT_WAIT_S = 1800

DEFAULT_TIME_LIMIT = 6.0
MEMORY_LIMIT = 1 << 30                  # address space per process
FILE_SIZE_LIMIT = 16 << 20
NPROC_LIMIT = 4                         # processes + threads per slot user (keeps slots from starving each other)
OUTPUT_CAP = 1 << 20                    # stdout bytes kept per case
STDERR_CAP = 64 << 10
CODE_CAP = 1 << 20
REPORT_FIELD_CAP = 1000
STDERR_TAIL_LINES = 20

PASS, FAIL, INFRA = "pass", "candidate_failure", "infrastructure_error"
VERDICT_NAMES = {"WA": "wrong answer", "RE": "runtime error", "TLE": "time limit exceeded",
                 "CE": "syntax error", "MISSING": "empty submission", "INFRA": "judge failure"}


class JudgeFailure(Exception):
    """The judge could not produce a result (not the submission's fault)."""


# ---------------------------------------------------------------- comparison
def _stripped_lines(text):
    return [line.strip() for line in text.strip().split("\n")]


def _decimals(line):
    try:
        return [Decimal(token) for token in line.split()]
    except (InvalidOperation, ValueError):
        return None


def outputs_match(actual, expected):
    got, want = _stripped_lines(actual), _stripped_lines(expected)
    if len(got) != len(want):
        return False
    for a, b in zip(got, want):
        if a == b:
            continue
        da, db = _decimals(a), _decimals(b)
        try:
            if da is None or db is None or da != db:
                return False
        except InvalidOperation:  # e.g. sNaN: malformed output, not a judge failure
            return False
    return True


# ---------------------------------------------------------------- tests on disk
def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def list_cases(task_dir):
    task_dir = Path(task_dir)
    if not task_dir.is_dir():
        raise JudgeFailure(f"no tests for task: {task_dir.name}")
    cases = []
    for inp in sorted(task_dir.glob("*.in")):
        out = inp.with_suffix(".out")
        if not out.is_file():
            raise JudgeFailure(f"missing expected output {task_dir.name}/{out.name}")
        cases.append((inp.stem, inp, out))
    if not cases:
        raise JudgeFailure(f"no test cases for task: {task_dir.name}")
    return cases


def tests_digest(task_dir):
    digest = hashlib.sha256()
    for name, inp, out in list_cases(task_dir):
        for path in (inp, out):
            digest.update(f"{name}{path.suffix}\0{sha256_bytes(path.read_bytes())}\n".encode())
    return digest.hexdigest()


# ---------------------------------------------------------------- slots
def _cgroup_cpus():
    try:
        quota, period = Path("/sys/fs/cgroup/cpu.max").read_text().split()
        if quota != "max":
            return max(1, int(int(quota) / int(period)))
    except (OSError, ValueError):
        pass
    return os.cpu_count() or 1


def n_slots():
    configured = os.environ.get("JUDGE_SLOTS")
    count = int(configured) if configured else _cgroup_cpus()
    return max(1, min(MAX_SLOTS, count))


def acquire_slot():
    """Lock one worker slot. The lock is released when the process exits."""
    LOCK_DIR.mkdir(mode=0o700, parents=True, exist_ok=True)
    deadline = time.monotonic() + SLOT_WAIT_S
    while True:
        for slot in range(n_slots()):
            fd = os.open(LOCK_DIR / f"{slot}.lock", os.O_RDWR | os.O_CREAT, 0o600)
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                return slot, fd
            except BlockingIOError:
                os.close(fd)
        if time.monotonic() > deadline:
            raise JudgeFailure("timed out waiting for a free judge slot")
        time.sleep(0.02)


def _processes_of(uid):
    pids = []
    for entry in Path("/proc").iterdir():
        if not entry.name.isdigit():
            continue
        try:
            if entry.stat().st_uid != uid:
                continue
            state = (entry / "stat").read_text().rsplit(")", 1)[1].split()[0]
        except (OSError, IndexError):
            continue
        if state != "Z":
            pids.append(int(entry.name))
    return pids


def kill_uid(uid):
    """SIGKILL every live process owned by uid, including detached daemons."""
    for _ in range(200):
        pids = _processes_of(uid)
        if not pids:
            return
        for pid in pids:
            try:
                os.kill(pid, signal.SIGKILL)
            except (ProcessLookupError, PermissionError):
                pass
        time.sleep(0.01)
    raise JudgeFailure(f"could not kill processes of uid {uid}")


def _remove(path):
    if path.is_dir() and not path.is_symlink():
        shutil.rmtree(path, ignore_errors=True)
    else:
        try:
            path.unlink()
        except FileNotFoundError:
            pass


class Slot:
    """A worker slot: one runner user, one work directory, one code directory."""

    def __init__(self, index):
        self.index = index
        self.uid = self.gid = RUNNER_UID_BASE + index
        self.work = WORK_ROOT / f"work-{index}"
        self.code_dir = WORK_ROOT / f"code-{index}"

    def _scrub(self):
        """Kill the runner's processes and delete everything it owns in shared dirs."""
        kill_uid(self.uid)
        for root in (WORK_ROOT, SHM_DIR):
            try:
                entries = list(root.iterdir())
            except OSError:
                continue
            for entry in entries:
                try:
                    owned = entry.lstat().st_uid == self.uid
                except OSError:
                    continue
                if owned or entry == self.work:
                    _remove(entry)

    def reset(self):
        self._scrub()
        self.work.mkdir(mode=0o700)
        os.chown(self.work, self.uid, self.gid)

    def write_code(self, code):
        """root:runner-k 0750 / 0640: this slot can read its code, other slots cannot."""
        _remove(self.code_dir)
        self.code_dir.mkdir(mode=0o750)
        os.chown(self.code_dir, 0, self.gid)
        self.code_dir.chmod(0o750)
        path = self.code_dir / "solution.py"
        path.write_bytes(code)
        os.chown(path, 0, self.gid)
        path.chmod(0o640)
        return path

    def release(self):
        self._scrub()
        _remove(self.code_dir)


# ---------------------------------------------------------------- execution
def _limits(time_limit):
    cpu_seconds = int(time_limit) + 2

    def apply():
        for limit, value in ((resource.RLIMIT_AS, MEMORY_LIMIT),
                             (resource.RLIMIT_CPU, cpu_seconds),
                             (resource.RLIMIT_FSIZE, FILE_SIZE_LIMIT),
                             (resource.RLIMIT_NPROC, NPROC_LIMIT),
                             (resource.RLIMIT_CORE, 0)):
            resource.setrlimit(limit, (value, value))
        try:  # prefer killing the submission over the judge if memory runs out
            with open("/proc/self/oom_score_adj", "w") as handle:
                handle.write("1000")
        except OSError:
            pass
    return apply


def _read_capped(handle, cap):
    handle.seek(0)
    data = handle.read(cap + 1)
    return data[:cap].decode("utf-8", "replace"), len(data) > cap


def _read_tail(handle, cap):
    """The last `cap` bytes, so a long stderr still ends with the traceback."""
    size = handle.seek(0, os.SEEK_END)
    handle.seek(max(0, size - cap))
    return handle.read(cap).decode("utf-8", "replace")


def run_case(slot, solution, case_in, case_out, time_limit):
    slot.reset()
    env = {"PATH": "/usr/local/bin:/usr/bin:/bin", "HOME": str(slot.work),
           "TMPDIR": str(slot.work), "LANG": "C.UTF-8", "PYTHONDONTWRITEBYTECODE": "1"}
    IO_DIR.mkdir(mode=0o700, parents=True, exist_ok=True)
    with open(case_in, "rb") as stdin, tempfile.TemporaryFile(dir=IO_DIR) as out, \
            tempfile.TemporaryFile(dir=IO_DIR) as err:
        start = time.monotonic()
        try:
            proc = subprocess.Popen(
                [sys.executable, "-I", str(solution)], stdin=stdin, stdout=out, stderr=err,
                cwd=slot.work, env=env, user=slot.uid, group=slot.gid, extra_groups=[],
                start_new_session=True, preexec_fn=_limits(time_limit), close_fds=True)
        except OSError as error:
            raise JudgeFailure(f"could not start submission: {error}") from error
        try:
            code = proc.wait(timeout=time_limit)
            timed_out = False
        except subprocess.TimeoutExpired:
            timed_out = True
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except (ProcessLookupError, PermissionError):
                proc.kill()
            code = proc.wait()
        elapsed = time.monotonic() - start
        kill_uid(slot.uid)
        stdout, overflow = _read_capped(out, OUTPUT_CAP)
        stderr = _read_tail(err, STDERR_CAP)
    case = {"time_s": round(elapsed, 3), "stdout": stdout, "stderr": stderr}
    if timed_out or code == -signal.SIGXCPU:
        case["verdict"] = "TLE"
    elif code == -signal.SIGXFSZ or overflow:
        case["verdict"] = "WA"
        case["note"] = "output exceeded the size limit"
    elif code != 0:
        case["verdict"] = "RE"
        if code == -signal.SIGKILL:
            case["note"] = "killed (possibly out of memory)"
    else:
        expected = Path(case_out).read_text(encoding="utf-8", errors="replace")
        case["verdict"] = "AC" if outputs_match(stdout, expected) else "WA"
    return case


# ---------------------------------------------------------------- results
def _clip(text, cap=REPORT_FIELD_CAP):
    text = text or ""
    return text if len(text) <= cap else text[:cap] + f"\n... [truncated, {len(text)} chars total]"


def _clip_tail(text, cap=REPORT_FIELD_CAP):
    """Like _clip but keeps the end (for stderr, where the traceback is last)."""
    text = text or ""
    return text if len(text) <= cap else f"[truncated, {len(text)} chars total] ...\n" + text[-cap:]


def _read_text(path):
    return Path(path).read_text(encoding="utf-8", errors="replace")


def _first_failure(cases, paths):
    failing = next((c for c in cases if c["verdict"] != "AC"), None)
    if failing is None:
        return None
    first = {"name": failing["name"], "verdict": failing["verdict"]}
    if failing["verdict"] in ("MISSING", "INFRA"):
        return first
    if failing["verdict"] == "CE":
        first["stderr_tail"] = _clip_tail(failing.get("stderr", ""))
        return first
    case_in, case_out = paths[failing["name"]]
    first["input"] = _clip(_read_text(case_in))
    if failing["verdict"] == "WA":
        first["expected"] = _clip(_read_text(case_out))
        first["actual"] = _clip(failing.get("stdout", ""))
    tail = "\n".join(failing.get("stderr", "").rstrip().splitlines()[-STDERR_TAIL_LINES:])
    first["stderr_tail"] = _clip_tail(tail)
    if failing.get("note"):
        first["note"] = failing["note"]
    return first


def format_report(suite, passed, total, first, error=None):
    """The bounded text an agent may see. Built only from the result fields."""
    title = f"{suite.upper()} TESTS"
    if error:
        return f"{title}: infrastructure error ({error})"
    lines = [f"{title}: {passed}/{total} passed"]
    if first is None:
        return lines[0]
    verdict = first["verdict"]
    lines.append(f"First failure: case {first['name']}: {verdict} "
                 f"({VERDICT_NAMES.get(verdict, verdict)})")
    for key, label in (("input", "input"), ("expected", "expected"), ("actual", "actual")):
        if key in first:
            lines += [f"--- {label} ---", first[key]]
    if verdict == "TLE":
        lines.append("(no result within the time limit)")
    if first.get("note"):
        lines.append(f"note: {first['note']}")
    if first.get("stderr_tail"):
        lines += ["--- stderr (last lines) ---" if verdict != "CE" else "--- error ---",
                  first["stderr_tail"]]
    return "\n".join(lines)


def judge_task(code, task_id, task_dir, time_limit, suite, tests_sha256=None, code_sha256=None):
    """Judge one submission. Raises JudgeFailure only for judge-side problems.

    `code` may be a bounded prefix of the submission; `code_sha256` is then the
    hash of the complete submission.
    """
    cases_on_disk = list_cases(task_dir)
    paths = {name: (inp, out) for name, inp, out in cases_on_disk}
    result = {"judge_version": JUDGE_VERSION, "suite": suite, "task_id": task_id,
              "tests_sha256": tests_sha256, "code_sha256": code_sha256 or sha256_bytes(code),
              "time_limit_s": time_limit}

    def every(verdict, **extra):
        return [{"name": name, "verdict": verdict, "time_s": 0.0, **extra}
                for name, _, _ in cases_on_disk]

    if not code.strip():
        cases = every("MISSING")
    elif len(code) > CODE_CAP:
        cases = every("CE", stderr=f"submission exceeds {CODE_CAP} bytes")
    else:
        try:
            compile(code, "solution.py", "exec")
            compile_error = None
        except (SyntaxError, ValueError, RecursionError, MemoryError) as error:
            compile_error = f"{type(error).__name__}: {error}"
        if compile_error:
            cases = every("CE", stderr=compile_error)
        else:
            slot_index, lock = acquire_slot()
            slot = Slot(slot_index)
            try:
                solution = slot.write_code(code)
                cases = [{"name": name,
                          **run_case(slot, solution, inp, out, time_limit)}
                         for name, inp, out in cases_on_disk]
            finally:
                slot.release()
                os.close(lock)
    verdicts = [case["verdict"] for case in cases]
    counts = {}
    for verdict in verdicts:
        counts[verdict] = counts.get(verdict, 0) + 1
    first = _first_failure(cases, paths)
    passed = verdicts.count("AC")
    result.update(
        status=PASS if passed == len(cases) else FAIL,
        passed=passed, total=len(cases), verdict_counts=counts,
        cases=[{"name": c["name"], "verdict": c["verdict"], "time_s": c["time_s"]} for c in cases],
        first_failure=first, report=format_report(suite, passed, len(cases), first))
    return result


def infra_result(error, suite=None, task_id=None, code_sha256=None, time_limit=None):
    return {"judge_version": JUDGE_VERSION, "suite": suite, "task_id": task_id,
            "tests_sha256": None, "code_sha256": code_sha256,
            "time_limit_s": time_limit, "status": INFRA, "passed": 0, "total": 0,
            "verdict_counts": {}, "cases": [], "first_failure": None, "error": error,
            "report": format_report(suite or "judge", 0, 0, None, error=error)}


# ---------------------------------------------------------------- commands
def _now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")


def _safe_member(name):
    parts = name.split("/")
    if len(parts) != 2 or any(not p or p.startswith(".") or p in ("..",) for p in parts):
        return None
    task_id, filename = parts
    if filename != "task.json" and not (filename.endswith(".in") or filename.endswith(".out")):
        return None
    return task_id, filename


def read_suite_meta():
    try:
        return json.loads(SUITE_META.read_text())
    except (OSError, ValueError) as error:
        raise JudgeFailure("no test suite loaded (run `judge load`)") from error


def cmd_load(args):
    staging = STATE_DIR / "suite.loading"
    _remove(staging)
    staging.mkdir(mode=0o700, parents=True)
    with tarfile.open(fileobj=sys.stdin.buffer, mode="r|") as archive:
        for member in archive:
            if member.isdir():
                continue
            target = _safe_member(member.name.removeprefix("./"))
            if not member.isfile() or target is None:
                raise JudgeFailure(f"unexpected archive member: {member.name}")
            task_id, filename = target
            task_dir = staging / task_id
            task_dir.mkdir(mode=0o700, exist_ok=True)
            source = archive.extractfile(member)
            fd = os.open(task_dir / filename, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(fd, "wb") as handle:
                shutil.copyfileobj(source, handle)
    tasks = {}
    for task_dir in sorted(staging.iterdir()):
        meta_path = task_dir / "task.json"
        meta = json.loads(meta_path.read_text()) if meta_path.exists() else {}
        tasks[task_dir.name] = {"n_cases": len(list_cases(task_dir)),
                                "time_limit_s": float(meta.get("time_limit_s", DEFAULT_TIME_LIMIT)),
                                "tests_sha256": tests_digest(task_dir)}
    if not tasks:
        raise JudgeFailure("the archive contained no tasks")
    _remove(SUITE_DIR)
    staging.rename(SUITE_DIR)
    overall = hashlib.sha256("".join(f"{t}:{m['tests_sha256']}\n"
                                     for t, m in sorted(tasks.items())).encode()).hexdigest()
    meta = {"judge_version": JUDGE_VERSION, "suite": args.suite, "loaded_at": _now(),
            "fingerprint": args.fingerprint,
            "n_tasks": len(tasks), "tests_sha256": overall, "tasks": tasks}
    fd = os.open(SUITE_META, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as handle:
        json.dump(meta, handle)
    return cmd_info(args)


def cmd_info(args):
    meta = read_suite_meta()
    print(json.dumps({"judge_version": JUDGE_VERSION, "suite": meta["suite"],
                      "fingerprint": meta.get("fingerprint"),
                      "loaded_at": meta["loaded_at"], "n_tasks": meta["n_tasks"],
                      "tests_sha256": meta["tests_sha256"], "slots": n_slots(),
                      "tasks": sorted(meta["tasks"])}))
    return 0


def read_submission(stream):
    """Hash all of stdin but keep at most CODE_CAP + 1 bytes for judging."""
    digest, kept = hashlib.sha256(), bytearray()
    while chunk := stream.read(1 << 16):
        digest.update(chunk)
        if len(kept) <= CODE_CAP:
            kept += chunk[:CODE_CAP + 1 - len(kept)]
    return bytes(kept), digest.hexdigest()


def cmd_run(args):
    code, code_sha = read_submission(sys.stdin.buffer)
    suite = None
    try:
        meta = read_suite_meta()
        suite = meta["suite"]
        task = meta["tasks"].get(args.task)
        if task is None:
            raise JudgeFailure(f"unknown task: {args.task}")
        time_limit = args.time_limit or task["time_limit_s"]
        result = judge_task(code, args.task, SUITE_DIR / args.task, time_limit, suite,
                            task["tests_sha256"], code_sha)
    except Exception as error:  # noqa: BLE001 - every judge-side failure becomes INFRA
        detail = str(error) if isinstance(error, JudgeFailure) else f"{type(error).__name__}: {error}"
        print(json.dumps(infra_result(detail, suite, args.task, code_sha, args.time_limit)))
        return 2
    print(json.dumps(result))
    return 0


SELFTEST_PROBE = r'''
import os, socket, subprocess
leaks = []
for path in ("/var/judge/suite.json", "/var/judge/suite"):
    try:
        open(path).read() if path.endswith(".json") else os.listdir(path)
        leaks.append("read " + path)
    except OSError:
        pass
try:
    os.listdir("/tmp")
    leaks.append("listed /tmp")
except OSError:
    pass
try:
    open("/tmp/leak", "w")
    leaks.append("wrote /tmp")
except OSError:
    pass
try:
    socket.create_connection(("1.1.1.1", 53), timeout=2)
    leaks.append("network")
except OSError:
    pass
try:
    os.setuid(0)
    leaks.append("setuid")
except OSError:
    pass
open(os.path.join(os.environ["TMPDIR"], "scratch"), "w").write("x")
open("/dev/shm/leftover", "w").write("x")
subprocess.Popen(["sleep", "300"], start_new_session=True)
print("ok" if not leaks else " ".join(leaks))
'''

SELFTEST_CASES = [
    ("correct", "a, b = map(int, input().split())\nprint(a + b)\n", None, PASS, None),
    ("wrong", "a, b = map(int, input().split())\nprint(abs(a + b))\n", None, FAIL, "WA"),
    ("syntax", "print(\n", None, FAIL, "CE"),
    ("empty", "", None, FAIL, "MISSING"),
    ("runtime", "raise SystemExit(3)\n", None, FAIL, "RE"),
    ("timeout", "while True:\n    pass\n", 1.0, FAIL, "TLE"),
    ("memory", "x = bytearray(3 << 30)\n", None, FAIL, "RE"),
    ("output", "import sys\nsys.stdout.write('x' * (4 << 20))\n", None, FAIL, "WA"),
]


def cmd_selftest(args):
    _remove(SELFTEST_DIR)
    (SELFTEST_DIR / "sum").mkdir(mode=0o700, parents=True)
    (SELFTEST_DIR / "probe").mkdir(mode=0o700)
    for name, inp, out in (("sum/01", "2 3\n", "5\n"), ("sum/02", "-4 1\n", "-3\n"),
                           ("probe/01", "\n", "ok\n")):
        (SELFTEST_DIR / f"{name}.in").write_text(inp)
        (SELFTEST_DIR / f"{name}.out").write_text(out)
    checks = []
    for name, code, limit, want_status, want_verdict in SELFTEST_CASES:
        result = judge_task(code.encode(), "selftest-sum", SELFTEST_DIR / "sum",
                            limit or 2.0, "selftest")
        got = result["first_failure"]["verdict"] if result["first_failure"] else None
        ok = result["status"] == want_status and got == want_verdict
        checks.append({"check": name, "ok": ok, "status": result["status"], "verdict": got})
    probe = judge_task(SELFTEST_PROBE.encode(), "selftest-probe", SELFTEST_DIR / "probe",
                       5.0, "selftest")
    leftovers = [uid for uid in range(RUNNER_UID_BASE, RUNNER_UID_BASE + MAX_SLOTS)
                 if _processes_of(uid)]
    stray = [str(p) for root in (WORK_ROOT, SHM_DIR) for p in root.iterdir()
             if p.lstat().st_uid >= RUNNER_UID_BASE]
    detail = probe["first_failure"].get("actual", "") if probe["first_failure"] else "ok"
    checks.append({"check": "isolation", "ok": probe["status"] == PASS, "detail": detail.strip()})
    checks.append({"check": "cleanup", "ok": not leftovers and not stray,
                   "detail": {"processes": leftovers, "files": stray}})
    _remove(SELFTEST_DIR)
    ok = all(check["ok"] for check in checks)
    print(json.dumps({"judge_version": JUDGE_VERSION, "ok": ok, "slots": n_slots(),
                      "checks": checks}))
    return 0 if ok else 1


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    load = sub.add_parser("load", help="load a test suite from a tar archive on stdin")
    load.add_argument("--suite", required=True)
    load.add_argument("--fingerprint", default=None, help="host-side identity of the archive")
    sub.add_parser("info", help="describe the loaded suite")
    run = sub.add_parser("run", help="judge source code from stdin")
    run.add_argument("--task", required=True)
    run.add_argument("--time-limit", type=float, default=None)
    sub.add_parser("selftest", help="built-in correctness and isolation checks")
    args = parser.parse_args(argv)
    handlers = {"load": cmd_load, "info": cmd_info, "run": cmd_run, "selftest": cmd_selftest}
    try:
        return handlers[args.command](args)
    except JudgeFailure as error:
        print(f"judge: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())

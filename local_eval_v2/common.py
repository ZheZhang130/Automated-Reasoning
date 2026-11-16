"""Shared paths and serialization; the committed v3 implementation stays untouched."""
import hashlib
import json
import os
import sys
import ctypes
import socket
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BASELINE = ROOT.parent / "local_baseline"
DATA = Path("E:/CSC2108Local/eval-v2")
ENDPOINT = "http://127.0.0.1:11435"
MODELS = ["qwen3.5:9b", "qwen2.5-coder:14b", "qwen2.5-coder:7b"]
os.environ.setdefault("MSWEA_SILENT_STARTUP", "1")
os.environ.setdefault("MSWEA_MODEL_RETRY_STOP_AFTER_ATTEMPT", "1")
os.environ.setdefault("MSWEA_GLOBAL_CONFIG_DIR", "E:/CSC2108Local/config")
sys.path.append(str(BASELINE))


def digest(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def save(path, obj):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(obj, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    os.replace(temp, path)


def on_e(path):
    path = Path(path).resolve()
    if path.drive.upper() != "E:":
        raise ValueError("Large artifacts must be on E:")
    return path


def alive(pid):
    if not pid:
        return False
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.OpenProcess.restype = ctypes.c_void_p
    handle = kernel.OpenProcess(0x1000, False, int(pid))
    if not handle:
        return ctypes.get_last_error() == 5
    try:
        code = ctypes.c_ulong()
        kernel.GetExitCodeProcess(ctypes.c_void_p(handle), ctypes.byref(code))
        return code.value == 259
    finally:
        kernel.CloseHandle(ctypes.c_void_p(handle))


class Lock:
    def __init__(self, path):
        self.path = Path(path)

    def __enter__(self):
        if self.path.exists():
            owner = read(self.path)
            if owner.get('host') != socket.gethostname() or alive(owner.get('pid')):
                raise RuntimeError('Work is already owned by a live process: ' + str(owner))
            save(self.path.with_name('stale-lock-' + str(time.time_ns()) + '.json'), owner)
            self.path.unlink()
        fd = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        with os.fdopen(fd, 'w') as target:
            json.dump({'pid': os.getpid(), 'host': socket.gethostname(), 'started': time.time()}, target)
        return self

    def __exit__(self, *args):
        if self.path.exists() and read(self.path).get('pid') == os.getpid():
            self.path.unlink()

"""judgekit command line.

    python -m judgekit up [--suite public|hidden] [--cpus N] [--force]
    python -m judgekit info [--suite ...]
    python -m judgekit run --task ID [--time-limit S] [--suite ...] < solution.py
    python -m judgekit selftest [--suite ...]
    python -m judgekit down [--suite ...]
"""
import argparse
import json
import sys

from judgekit import Judge, JudgeError


def main(argv=None):
    parser = argparse.ArgumentParser(prog="judgekit", description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("up", "info", "run", "selftest", "down"):
        cmd = sub.add_parser(name)
        cmd.add_argument("--suite", default="public", choices=["public", "hidden"])
        cmd.add_argument("--cpus", type=int, default=4)
        if name == "up":
            cmd.add_argument("--force", action="store_true", help="recreate the container")
            cmd.add_argument("--tasks", nargs="*", help="load only these task IDs")
        if name == "run":
            cmd.add_argument("--task", required=True)
            cmd.add_argument("--time-limit", type=float)
    args = parser.parse_args(argv)
    judge = Judge(args.suite, cpus=args.cpus, tasks=getattr(args, "tasks", None))
    try:
        if args.command == "up":
            info = judge.up(force=args.force)
            info["tasks"] = len(info["tasks"])
            print(json.dumps(info))
        elif args.command == "info":
            print(json.dumps(judge.info()))
        elif args.command == "run":
            result = judge.run(args.task, sys.stdin.buffer.read(), args.time_limit)
            print(json.dumps(result))
            return 0 if result["status"] != "infrastructure_error" else 2
        elif args.command == "selftest":
            result = judge.selftest()
            print(json.dumps(result, indent=2))
            return 0 if result["ok"] else 1
        else:
            judge.down()
    except JudgeError as error:
        print(f"judgekit: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())

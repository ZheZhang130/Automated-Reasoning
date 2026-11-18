#!/bin/sh
# One command to reproduce the judge environment from a fresh clone.
#
#   ./setup.sh            build tasks/, the judge image, start judge-public, run the selftest
#   ./setup.sh --hidden   also build hidden/ and start judge-hidden (evaluation owner)
#
# Needs python3 (3.10+), a running Docker engine and network access on the first run.
set -eu
cd "$(dirname "$0")"

HIDDEN=""
[ "${1:-}" = "--hidden" ] && HIDDEN="--hidden"

DOCKER="${DOCKER:-$(command -v docker || echo "$HOME/.orbstack/bin/docker")}"
"$DOCKER" info >/dev/null 2>&1 || { echo "Docker engine is not running ($DOCKER)" >&2; exit 1; }
IMAGE="$(python3 -c 'import judgekit; print(judgekit.IMAGE)')"

echo "== 1/4 data (pinned LiveCodeBench revision, checked against manifests/)"
python3 build_data.py $HIDDEN

echo "== 2/4 image $IMAGE"
"$DOCKER" build -q -t "$IMAGE" . >/dev/null

echo "== 3/4 judge container(s)"
python3 -m judgekit up --force
[ -n "$HIDDEN" ] && python3 -m judgekit up --suite hidden --force

echo "== 4/4 selftest"
python3 -m judgekit selftest | python3 -c 'import json,sys; r=json.load(sys.stdin); print("selftest", "OK" if r["ok"] else "FAILED"); sys.exit(0 if r["ok"] else 1)'

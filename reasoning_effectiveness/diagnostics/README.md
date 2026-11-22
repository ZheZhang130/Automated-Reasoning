# Post-hoc evaluation diagnostics (not part of the frozen scoring)

The team judge compares outputs exactly: lines must match exactly or as equal lists of `Decimal`s. Two
selected tasks need something else:

* `lcb-atcoder-abc392_d` accepts absolute or relative error ≤ 1e-8 → `tolerance_check.py`.
* `lcb-atcoder-abc396_e` accepts any minimum-sum valid sequence → `abc396_e_checker.py` (checks every XOR constraint plus the reference sum).

Both scripts run inside a disposable, network-less, read-only container. The candidate is mounted at `/c`, the hidden cases at `/h` and the script at `/d`, and they print only pass/fail counts. Example (Git Bash on Windows):

```sh
MSYS_NO_PATHCONV=1 docker run --rm --network none --read-only --memory 1g --cpus 1 --pids-limit 64 \
  --cap-drop ALL --security-opt no-new-privileges --user 65534:65534 --tmpfs /tmp \
  -v "<run dir>:/c:ro" -v "<study>/judge/hidden/<task>:/h:ro" -v "<this dir>:/d:ro" \
  python:3.11-slim-bookworm python3 -I /d/tolerance_check.py
```

These results are reported as a sensitivity analysis next to the official frozen-judge scores. They were
never shown to any model, and nothing was tuned on them.

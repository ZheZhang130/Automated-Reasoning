#!/usr/bin/bash
# Create feat/csc2108-final-agent from the final development commit and the prepared tree, WITHOUT checking it out
# (the development worktree keeps serving running batches). Usage: make_final_branch.sh MESSAGE_FILE
set -euo pipefail
S="C:/Users/SPACEJ~1/AppData/Local/Temp/claude/6526d96b0cdf8535/15a49ef6-108f-4b73-a73a-37a12051ded3/scratchpad"
REPO="/e/VS Code Projects/CSC2108Project/ar-pass2"
cd "$REPO"
if git show-ref --verify --quiet refs/heads/feat/csc2108-final-agent || git ls-remote --exit-code --heads origin feat/csc2108-final-agent >/dev/null 2>&1; then
  echo "feat/csc2108-final-agent already exists; refusing to overwrite" >&2; exit 3
fi
DEV=$(git rev-parse feat/csc2108-contract-diagnosis-pass2)
GIT_DIR=$(cd "$REPO" && git rev-parse --absolute-git-dir)
export GIT_INDEX_FILE="$S/final.index"
rm -f "$GIT_INDEX_FILE"
git read-tree "$DEV"
(cd "$S/final" && git --git-dir="$GIT_DIR" --work-tree="$S/final" add -A .)
TREE=$(git write-tree)
COMMIT=$(git commit-tree "$TREE" -p "$DEV" -F "$1")
unset GIT_INDEX_FILE
rm -f "$S/final.index"
git branch feat/csc2108-final-agent "$COMMIT"
echo "dev=$DEV final=$COMMIT tree=$TREE"
git diff --stat "$DEV" "$COMMIT" | tail -3

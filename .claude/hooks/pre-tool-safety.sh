#!/bin/bash
# Pre-tool safety hook — block obviously dangerous commands before execution.
# Wire in .claude/settings.json or .claude/settings.local.json under PreToolUse.

COMMAND="$1"

DANGEROUS_PATTERNS=(
  "rm -rf /"
  "rm -rf /*"
  "rm -rf ~"
  "rm -rf \\\$HOME"
  "rm -rf ."
  "DROP DATABASE"
  "DROP TABLE"
  "TRUNCATE TABLE"
  "git push --force main"
  "git push --force master"
  "git push -f main"
  "git push -f master"
  "git push --force-with-lease main"
  "git reset --hard origin"
  "git clean -fdx"
  "shutdown"
  "halt"
  "init 0"
  "init 6"
  "dd if=.* of=/dev/"
)

for pattern in "${DANGEROUS_PATTERNS[@]}"; do
  if echo "$COMMAND" | grep -qiE "$pattern"; then
    echo "BLOCKED: dangerous command pattern: $pattern"
    echo "If you really need to run this, do it manually outside Claude."
    exit 1
  fi
done

# Soft-warn about secrets / env files (not blocked, just flagged)
if echo "$COMMAND" | grep -qE "\.env( |\$|/)"; then
  echo "WARNING: command references .env — confirm no secrets exposed."
fi

# Soft-warn about raw biometric image writes (TANIK-specific)
if echo "$COMMAND" | grep -qE "cv2\.imwrite|imageio\.imwrite|Image\.save" && echo "$COMMAND" | grep -qE "/iris/|/fingerprint/|enroll|verify"; then
  echo "WARNING: command appears to write a biometric image to disk — TANIK never persists raw images."
fi

exit 0

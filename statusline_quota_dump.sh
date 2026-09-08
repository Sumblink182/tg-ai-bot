#!/bin/bash
# Antigravity CLI statusline script that ALSO dumps the quota JSON to disk.
# Based on the official statusline contract:
#   https://antigravity.google/docs/cli/statusline/
# The TUI pipes a JSON payload (containing a `quota` object with
# gemini-5h / gemini-weekly / 3p-5h / 3p-weekly buckets) to this script's
# stdin on every agent-state change. We persist it so that external tools
# (e.g. tg-ai-bot /status) can read the weekly quota bucket, which is not
# exposed via the local GetUserStatus RPC.
#
# Install:
#   1. Save as ~/.gemini/antigravity-cli/statusline.sh && chmod +x
#   2. Add to ~/.gemini/antigravity-cli/settings.json:
#        "statusLine": { "type": "command", "command": "~/.gemini/antigravity-cli/statusline.sh" }
#   3. Restart agy or run /clear.

# Hard-cap the stdin read (the runner kills slow scripts; see community notes)
JSON_INPUT="{}"
if [ ! -t 0 ]; then
  JSON_INPUT=$(timeout 0.25 cat 2>/dev/null || true)
fi
exec 0</dev/null
[ -z "$JSON_INPUT" ] && JSON_INPUT="{}"

# Dump for external consumers (bot /status weekly quota)
mkdir -p "${HOME}/.gemini/antigravity-cli" 2>/dev/null
printf '%s' "$JSON_INPUT" > "${HOME}/.gemini/antigravity-cli/.statusline_quota.json" 2>/dev/null

# --- minimal statusline rendering (model · state · quota) -------------------
if command -v jq >/dev/null 2>&1; then
  MODEL=$(printf '%s' "$JSON_INPUT" | jq -r '.model.display_name // .model.name // empty' 2>/dev/null)
  STATE=$(printf '%s' "$JSON_INPUT" | jq -r '.agent_state // "idle"' 2>/dev/null)
  Q5H=$(printf '%s' "$JSON_INPUT" | jq -r '.quota["gemini-5h"].remaining_fraction // empty' 2>/dev/null)
  QWK=$(printf '%s' "$JSON_INPUT" | jq -r '.quota["gemini-weekly"].remaining_fraction // empty' 2>/dev/null)
  LINE="◆ ${MODEL:-agy} · ${STATE}"
  [ -n "$Q5H" ] && LINE="$LINE · 5h $(awk -v q="$Q5H" 'BEGIN{printf "%.0f%%", q*100}')"
  [ -n "$QWK" ] && LINE="$LINE · 7d $(awk -v q="$QWK" 'BEGIN{printf "%.0f%%", q*100}')"
  echo "$LINE"
else
  echo "◆ agy"
fi

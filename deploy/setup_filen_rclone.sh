#!/bin/bash
# One-time setup: authenticate rclone against Filen.
# Exports an API key via the Filen CLI, then writes ~/.config/rclone/rclone.conf.
# Credentials are read interactively and passed via env/stdin, never as argv.
set -euo pipefail
umask 077

BIN="$HOME/bin"
CONF_DIR="$HOME/.config/rclone"
CONF="$CONF_DIR/rclone.conf"
REMOTE_DIR="bureau-backups"

command -v "$BIN/filen"  >/dev/null || { echo "missing $BIN/filen"; exit 1; }
command -v "$BIN/rclone" >/dev/null || { echo "missing $BIN/rclone"; exit 1; }

read -rp  "Filen email: " FILEN_CLI_EMAIL
read -rsp "Filen password: " FILEN_CLI_PASSWORD; echo
read -rp  "Filen 2FA code (leave empty if 2FA is off): " FILEN_CLI_2FA_CODE
export FILEN_CLI_EMAIL FILEN_CLI_PASSWORD
[ -n "$FILEN_CLI_2FA_CODE" ] && export FILEN_CLI_2FA_CODE || unset FILEN_CLI_2FA_CODE

echo "Exporting API key from Filen..."
RAW=$("$BIN/filen" --skip-update --quiet export-api-key 2>&1)
# pick the longest token in the output; the API key is a long opaque string
API_KEY=$(printf "%s" "$RAW" | tr -s "[:space:]" "\n" | awk "{ if (length(\$0) > length(m)) m = \$0 } END { print m }")
if [ "${#API_KEY}" -lt 32 ]; then
  echo "Could not parse an API key from filen output:"
  printf "%s\n" "$RAW"
  exit 1
fi
echo "Got API key (${#API_KEY} chars)."

mkdir -p "$CONF_DIR"
OBS_PW=$(printf "%s\n" "$FILEN_CLI_PASSWORD" | "$BIN/rclone" obscure -)
OBS_KEY=$(printf "%s\n" "$API_KEY" | "$BIN/rclone" obscure -)
cat > "$CONF" <<EOF
[filen]
type = filen
email = $FILEN_CLI_EMAIL
password = $OBS_PW
api_key = $OBS_KEY
EOF
chmod 600 "$CONF"
echo "Wrote $CONF"

echo "Verifying access..."
"$BIN/rclone" lsd filen: >/dev/null
"$BIN/rclone" mkdir "filen:$REMOTE_DIR"
"$BIN/rclone" lsd "filen:" | sed "s/^/  /"

# the Filen CLI is no longer needed for the nightly job; drop any saved creds
"$BIN/filen" --skip-update logout >/dev/null 2>&1 || true
echo
echo "OK. rclone can now reach filen:$REMOTE_DIR"

#!/bin/bash
# One-time: gzip and upload the pre-existing local dumps to Filen, verify by
# hash, then delete the local originals in ~/. Leaves ~/bak/ untouched.
set -euo pipefail
umask 077

RCLONE="$HOME/bin/rclone"
REMOTE="filen:bureau-backups/legacy"
STAGE="$HOME/backlog-stage"

shopt -s nullglob
SRC=( "$HOME"/infinita-db-data-*.json "$HOME"/bak/*-backup.json )
echo "${#SRC[@]} files to archive"
[ "${#SRC[@]}" -gt 0 ] || exit 0

mkdir -p "$STAGE"
for f in "${SRC[@]}"; do
    out="$STAGE/$(basename "$f").gz"
    [ -f "$out" ] || gzip -9c "$f" > "$out"
done
echo "staged $(ls "$STAGE" | wc -l) files, $(du -sh "$STAGE" | cut -f1)"

"$RCLONE" copy --transfers 4 "$STAGE" "$REMOTE"

# verify every staged file against the remote by hash (single listing pass)
"$RCLONE" check --one-way "$STAGE" "$REMOTE"

echo "all files verified on remote; removing local originals in ~/ (keeping ~/bak/)"
rm -f "$HOME"/infinita-db-data-*.json
rm -rf "$STAGE"
echo "done. $(df -h "$HOME" | tail -1)"

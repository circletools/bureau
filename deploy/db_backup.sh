#!/bin/bash
# Nightly DB backup for infinita bureau -> Filen (via rclone).
# Dumps into a staging dir, uploads, verifies by hash, then keeps the local copy
# for KEEP_LOCAL_DAYS. Remote history is never pruned (~500 KB/night).
set -euo pipefail
umask 077

RCLONE="$HOME/bin/rclone"
PYTHON="$HOME/.virtualenvs/bureau/bin/python"
PROJECT="$HOME/bureau"
WORK="$HOME/backups"
STAGE="$WORK/.staging"
REMOTE="filen:bureau-backups"
DB="infinita_bureau"
KEEP_LOCAL_DAYS=7
# healthchecks.io dead-man's-switch ping URL, one line, mode 600.
# absent file = pings disabled (the script still works).
HC_URL_FILE="$HOME/.hc_backup_url"

HC_URL=""
[ -r "$HC_URL_FILE" ] && HC_URL=$(head -1 "$HC_URL_FILE")

# hc <suffix>: "start", a numeric exit code, or empty for success
hc() {
    [ -n "$HC_URL" ] || return 0
    curl -fsS -m 10 --retry 3 -o /dev/null "$HC_URL${1:+/$1}" || true
}

# any non-zero exit (set -e, failed verification, dump error) alerts immediately
on_exit() { rc=$?; [ "$rc" -eq 0 ] || hc "$rc"; }
trap on_exit EXIT

STAMP=$(date -u +%Y-%m-%dT%H%M%SZ)
YEAR=$(date -u +%Y)
JSON="bureau-dumpdata-$STAMP.json.gz"
PGD="bureau-pgdump-$STAMP.dump"

hc start

rm -rf "$STAGE"
mkdir -p "$STAGE"

# 1. Django logical dump: portable, restores with loaddata (also into sqlite)
cd "$PROJECT"
"$PYTHON" manage.py dumpdata --natural-foreign --natural-primary \
    -e contenttypes -e auth.Permission --indent 2 | gzip -9 > "$STAGE/$JSON"
gzip -t "$STAGE/$JSON"
OBJECTS=$(gzip -dc "$STAGE/$JSON" | "$PYTHON" -c "import json,sys;print(len(json.load(sys.stdin)))")
[ "$OBJECTS" -gt 100 ] || { echo "dumpdata suspiciously small: $OBJECTS objects" >&2; exit 1; }

# 2. Postgres native dump: faithful (schema, sessions, permissions)
pg_dump -Fc --no-owner --no-privileges "$DB" > "$STAGE/$PGD"
pg_restore -l "$STAGE/$PGD" >/dev/null

# 3. Upload and verify by hash against the remote
"$RCLONE" copy "$STAGE" "$REMOTE/$YEAR"
"$RCLONE" check --one-way "$STAGE" "$REMOTE/$YEAR"

# 4. Keep a local copy, prune old ones (remote keeps everything)
mv "$STAGE/$JSON" "$STAGE/$PGD" "$WORK/"
rmdir "$STAGE"
find "$WORK" -maxdepth 1 -type f -name "bureau-*" -mtime +$KEEP_LOCAL_DAYS -delete

hc ""

echo "backup ok: $OBJECTS objects, $(du -h "$WORK/$JSON" | cut -f1) json.gz + $(du -h "$WORK/$PGD" | cut -f1) pgdump -> $REMOTE/$YEAR/"

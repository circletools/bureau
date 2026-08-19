# deploy scripts (djangoeurope / infinita)

Live on the server in `~/` (user `infinita`). Setup, remote layout and restore
commands are documented in the main README, section
"2026-08-19, nightly db backup to filen.io".

- `setup_filen_rclone.sh` — one-time, interactive. Prompts for filen.io
  credentials, exports an API key, writes `~/.config/rclone/rclone.conf`.
  Rerun after a filen password change.
- `db_backup.sh` — nightly cron job (05:00 UTC). Dumps, verifies, uploads to
  filen.io, keeps 7 days locally.
- `migrate_backlog.sh` — one-off, already run 2026-08-19. Uploaded the pre-filen
  local dumps to `filen:bureau-backups/legacy/`.

No credentials belong in these files: `db_backup.sh` and `migrate_backlog.sh`
read them from `~/.config/rclone/rclone.conf` (mode 600, written by the setup
script), `setup_filen_rclone.sh` reads them from the terminal.

# bureau
simple school management database


## Preliminary Steps for installing on djangoeurope

- use djangoeurope's one-click installer to create a new django project, "bureau"

- log into the server using your djangoeurope ssh user

- check out bureau distribution from git into bureau.git
	- ```~$ git clone https://github.com/dturing/bureau.git bureau.git```

- go to ~/bureau, link the people module from the git checkout:
	- ```~/bureau$ ln -s ../bureau.git/people/ people```

- link bureau.git/templates/admin into bureau/dproject/templates
	- ```$ cd ~/bureau/dproject/templates```
	- ```$ ln -s ~/bureau.git/templates/admin .```

- install requirements
    - ```~bureau$ pip3 install -r ../bureau.git/requirements.txt```

- edit config/settings/common.py,

	- add the "settings" module from bureau.git/bureau/settings.py
		```
		def settings(request):
		    """
		    Put selected settings variables into the default template context
		    """
		    from django.conf import settings
		    return settings.GLOBAL_SETTINGS
		```
	- add 'people' to LOCAL_APPS, 
		(DONT) remove 'imprint'; 
		(DONT) remove 'django.contrib.sites' from DJANGO_APPS
	- remove all LANGUAGES except de, set LANGUAGE_CODE to 'de'
	- add 'config.settings.common.settings' to TEMPLATES[OPTIONS][context_processors]
	- add sensible GLOBAL_SETTINGS

- edit config/urls.py
	- add
		```
		from django.views.generic.base import RedirectView
		from django.conf import settings
		```
	- modify the ^$ urlpattern to read
		```url(r'^$', RedirectView.as_view(url='/admin')),```
	- add to urlpatterns:
		```url(r'^people/', include('people.urls')),```
	- add at bottom of file:
		```
		admin.site.site_header = settings.GLOBAL_SETTINGS['SCHOOL_NAME']+" Bureau"
		admin.site.index_title = "Verwaltung"
		```


- makemessages, compilemessages
	- ```$ cd people```
	- ```$ django-admin makemessages --all```
	- ```$ django-admin compilemessages```

- migrate
	- ```$ python manage.py makemigrations people```
	- ```$ python manage.py migrate```


## Caveats

### SSL error on djangoeurope.com

if you get a 500 Bad Request / "Contradictory scheme headers" error after enabling an SSL certificate on djangoeurope, please observe https://panel.djangoeurope.com/support/doc/http2https


## Random notes

### 2021-10-25, for infinita on djangoeurope,

- add admin email in djangoeurope panel and enter itno settings
- manually? install requirements:
	pip3 install xlsxwriter
	pip3 install djangorestframework

- settings: 
   DEFAULT_AUTO_FIELD='django.db.models.AutoField'

### 2022-06-27, for infinita/djangoeurope dropbox backup

(superseded 2026-08-19, see "nightly db backup to filen.io" below. the dropbox token
expired; uploads had been failing silently since late 2023.)

setup a dropbox app with file write permissions,
https://www.xmodulo.com/access-dropbox-command-line-linux.html

db_backup.sh:
'''
#!/bin/bash
BACKUPFILE=~/infinita-db-data-$(date -Isecond).json
cd ~/bureau
source ./.envrc
python manage.py dumpdata > $BACKUPFILE
cd ~
./dropbox_uploader.sh upload $BACKUPFILE /
rm $BACKUPFILE
'''

crontab -e
'''
0 5 * * * bash /home/infinita/db_backup.sh
'''


### to change password:

'''
manage.py changepassword admin
'''



### 2026-08-19, nightly db backup to filen.io

replaces the dropbox backup. uses rclone's filen backend (upstream since rclone
v1.73) instead of the filen CLI, which is sunset.

server setup (~, user infinita, no root needed):

- `~/bin/rclone` — rclone v1.75.0, pinned:
'''
mkdir -p ~/bin && cd /tmp
curl -sfLO https://downloads.rclone.org/v1.75.0/rclone-v1.75.0-linux-amd64.zip
unzip -oq rclone-v1.75.0-linux-amd64.zip
install -m 755 rclone-v1.75.0-linux-amd64/rclone ~/bin/rclone
'''

- `~/bin/filen` — filen rust CLI, only needed to export the API key that the
  rclone backend requires:
'''
curl -sfL -o ~/bin/filen https://github.com/FilenCloudDienste/filen-cli-releases/releases/download/0.2.7/filen-cli-0.2.7-x86_64-unknown-linux-gnu
chmod +x ~/bin/filen
'''

- `~/setup_filen_rclone.sh` — one-time, interactive. prompts for filen
  email/password/2FA, runs `filen export-api-key`, writes
  `~/.config/rclone/rclone.conf` (mode 600) with password and api_key passed
  through `rclone obscure`. rerun this after a filen password change (the API
  key must be re-exported too).

- `~/db_backup.sh` — nightly. dumps to `~/backups/.staging`, verifies each dump
  (`gzip -t` + json object count, `pg_restore -l`), uploads with `rclone copy`,
  confirms with `rclone check --one-way`, then keeps local copies 7 days.
  produces two files per night, ~500 KB total:
    - `bureau-dumpdata-<stamp>.json.gz` — `manage.py dumpdata`, restores with
      loaddata (also into sqlite for local dev)
    - `bureau-pgdump-<stamp>.dump` — `pg_dump -Fc`, faithful incl. schema

  calls `~/.virtualenvs/bureau/bin/python` directly rather than sourcing
  `.envrc`, which fails under `set -u`. pg_dump needs no password (peer auth).

- crontab:
'''
0 5 * * * bash /home/infinita/db_backup.sh >> /home/infinita/backups/backup.log
'''
  stdout goes to the log, stderr to cron mail (`/var/mail/infinita`).

- alerting: healthchecks.io dead-man's-switch. the script pings start / success
  / exit-code, so both a failed run and a run that never happens raise an alert.
  the ping URL lives in `~/.hc_backup_url` (mode 600, not in git); if that file
  is missing the script still runs, just without pings. check period 1 day.

  server mail is not used for alerting: postfix delivers direct-to-MX with no
  DKIM and no DMARC for infinita.circletools.org (SPF does list s30), and
  microsoft 365 junks it — verified 2026-08-19 with two test messages.

remote layout on filen (the school's filen account):
'''
bureau-backups/<year>/   nightly dumps, never pruned (~200 MB/year)
bureau-backups/legacy/   the 185 pre-2026-08-19 dumps, gzipped
'''

restore:
'''
~/bin/rclone lsf filen:bureau-backups/2026/            # pick a dump
~/bin/rclone copy filen:bureau-backups/2026/<file> .
# postgres, full restore:
pg_restore -d infinita_bureau --clean --if-exists <file>.dump
# or django-level, into an empty/migrated db:
gzip -dc <file>.json.gz > d.json && python manage.py loaddata d.json
'''

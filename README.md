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


### 2021-10-25, for infinita on djangoeurope,

- add admin email in djangoeurope panel and enter itno settings
- manually? install requirements:
	pip3 install xlsxwriter
	pip3 install djangorestframework

- settings: 
   DEFAULT_AUTO_FIELD='django.db.models.AutoField'

### 2022-06-27, for infinita/djangoeurope dropbox backup

setup a dropbox app with file write permissions,
https://www.xmodulo.com/access-dropbox-command-line-linux.html

db_backup.sh:
	#!/bin/bash
	BACKUPFILE=~/infinita-db-data-$(date -Isecond).json
	cd ~/bureau
	source ./.envrc
	python manage.py dumpdata > $BACKUPFILE
	cd ~
	./dropbox_uploader.sh upload $BACKUPFILE /
	rm $BACKUPFILE

crontab -e
	0 5 * * * bash /home/infinita/db_backup.sh


###
 change password:

 # manage.py changepassword admin


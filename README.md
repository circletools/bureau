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
	- add 'people' to LOCAL_APPS, remove 'imprint'; remove 'django.contrib.sites' from DJANGO_APPS
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
	- ```$ django-admin.py makemessages```
	- ```$ django-admin.py compilemessages```

- migrate
	- ```$ python manage.py makemigrations people```
	- ```$ python manage.py migrate```


## Caveats

### SSL error on djangoeurope.com

if you get a 500 Bad Request / "Contradictory scheme headers" error after enabling an SSL certificate on djangoeurope, please observe https://panel.djangoeurope.com/support/doc/http2https


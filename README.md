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

- edit config/settings/urls.py
	- add
		```
		from django.views.generic.base import RedirectView
		from django.conf import settings
		```
	- modify the ^$ urlpattern to read
		```url(r'^$', RedirectView.as_view(url='/admin')),```
	- add to urlpatterns:
		```url(r'^people/', include('people.urls')),```

- makemessages, compilemessages
	- ```$ mv people/locale/de/LC_MESSAGES/django.po dproject/locale/de/LC_MESSAGES/```
	- ```$ python manage.py makemessages```
	- ```$ python manage.py compilemessages```

- migrate
	- ```$ python manage.py makemigrations people```
	- ```$ python manage.py migrate```




from django.conf.urls import include,url
from django.contrib import admin
from django.views.generic.base import RedirectView
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    url(r'^people/', include('people.urls')),
    url(r'^admin/', admin.site.urls),
    url(r'^$', RedirectView.as_view(url='/admin'))
#    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework'))
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

admin.site.site_header = settings.GLOBAL_SETTINGS['SCHOOL_NAME']+" Bureau"

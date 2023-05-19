
from django.urls import include,re_path
from django.contrib import admin
from django.views.generic.base import RedirectView
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    re_path(r'^people/', include('people.urls')),
    re_path(r'^admin/', admin.site.urls),
    re_path(r'^$', RedirectView.as_view(url='/admin'))
#    re_path(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework'))
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

admin.site.site_header = settings.GLOBAL_SETTINGS['SCHOOL_NAME']+" Bureau"
admin.site.index_title = "Verwaltung"

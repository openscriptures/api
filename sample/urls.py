from django.conf.urls.defaults import *
from django.contrib import admin

from openscriptures_api_texts import urls as ost_urls


admin.autodiscover()

urlpatterns = patterns('',
    (r'^texts/', include(ost_urls)),
    
    # Default login url
    (r'^accounts/login/$', 'django.contrib.auth.views.login'),
    (r'^accounts/logout/$', 'django.contrib.auth.views.logout'),

    # Uncomment the next line to enable the admin:
    (r'^admin/', include(admin.site.urls)),
)

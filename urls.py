from django.conf.urls.defaults import *
from models import *

urlpatterns = patterns('',
    (r'^rest/osis/([^/]+)', 'api.rest.views.get_osis'),
)

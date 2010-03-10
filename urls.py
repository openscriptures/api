from django.conf.urls.defaults import *
from models import *
import re
import string



urlpatterns = patterns('',
    (r'^rest/passage/(?P<osis_ref>.+)$', 'api.rest.views.passage'),
)



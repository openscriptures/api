from django.conf.urls.defaults import patterns


# osis module can define a parser, osisRef object

urlpatterns = patterns('',
    (r'^rest/passage/(?P<osis_ref>.+)$', 'api.rest.views.passage'),
)


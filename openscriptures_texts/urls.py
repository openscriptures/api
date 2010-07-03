from django.conf.urls.defaults import patterns


# osis module can define a parser, osisRef object

urlpatterns = patterns('',
    (r'^rest/passage/(?P<osis_ref>.+)$', 'openscriptures_texts.rest.views.passage'),
)



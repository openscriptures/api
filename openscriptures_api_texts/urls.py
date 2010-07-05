from django.conf.urls.defaults import patterns


# osis module can define a parser, osisRef object

urlpatterns = patterns('',
    (r'^passage/(?P<osis_ref>.+)$', 'openscriptures_api_texts.views.passage'),
)



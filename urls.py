from django.conf.urls.defaults import *
from models import *
import re
import string



urlpatterns = patterns('',
    #(
    #    #re.compile(... ,re.VERBOSE)
    #    re.sub(r'\s+', '', ur"""^rest/osis/
    #        (?P<osis_work>
    #            (?P<type>\w+)
    #            (?:\.(?P<language>\w+))?
    #            (?:\.(?P<slug1>\w+))?
    #            (?:\.(?P<slug2>\w+))?
    #            (?:\.(?P<publish_date>\w+))?
    #        ):
    #        (?P<start_osis_id>
    #            .+?
    #        )
    #        (?:-
    #            (?P<end_osis_id>
    #               .+? 
    #            )
    #        )?$
    #    """),
    #    'api.rest.views.get_osis'
    #)
    #(r'^rest/osis/(?P<osis_work>.+?):(?P<start_osis_id>.+?)(?:-(?P<end_osis_id>.+?))?$', 'api.rest.views.get_osis'),
    (r'^rest/osis/(?P<osis_ref>.+)$', 'api.rest.views.get_osis'),
    #Bible.en.Publisher.ABC.2010
    #(?P<section>[-\w]+)/$
)



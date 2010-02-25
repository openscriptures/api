from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.http import Http404
from api.models import *


def get_osis(request, osis_id):
    try:
        structure = TokenStructure.objects.get(osis_id = osis_id)
    except:
        raise Http404
    
    tokens = structure.get_tokens()
    structures = TokenStructure.objects.all()
    
    return render_to_response('passage_lookup.html', {
        'osis_id': osis_id,
        'structure': structure,
        'tokens': tokens,
        'structures': structures
    })
    

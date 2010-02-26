from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.http import Http404
from api.models import *
#import api.osis
from api import osis
import json

#TODO: allow range
def get_osis(request, osis_ref): #MORE #osis_work, osis_ref_start, osis_ref_end
    parsed = osis.parse_osis_ref(osis_ref)
    
    
    
    return HttpResponse(json.dumps(parsed))
    
    
    #todo: Query the OSIS work
    try:
        work = Work.objects.get(
            osis_id = osis_work
        )
        main_work = work
        if work.variants_for_work is not None:
            main_work = work.variants_for_work
    except:
        raise Http404
    
    # Get all of the structures for a given work including their start_token/end_token
    # Ignore all structures that don't have start_token
    # Then for the tokens that exist the requested structure(s), then query
    # all stuctures that overlap the positions of the start_token and end_token
    
    
    workStructures = TokenStructure.objects.filter(
        osis_id = osis_id,
        work = main_work
    ).extra(where="variant_bits & %s != 0", params=[work.variant_bit])
    
    
    
    
    
    tokens = structure.get_tokens()
    
    return render_to_response('passage_lookup.html', {
        'osis_id': osis_id,
        'structure': structure,
        'tokens': tokens,
        'structures': workStructures
    })
    

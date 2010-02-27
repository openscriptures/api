# coding: utf8 #

from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.http import Http404
from api.models import *
from django.db.models import Q
from api import osis
import json

#BAD: This should be in the model for a Work? After getting work, then pass-in osisRef
def get_osis(request, osis_ref): #MORE #osis_work, osis_ref_start, osis_ref_end
    osis_ref_parsed = osis.parse_osis_ref(osis_ref)
    #return HttpResponse(str(osis_ref_parsed['work_prefix']))
    
    #todo: Query the OSIS work
    try:
        kwargs = osis_ref_parsed['work_prefix']
        #If variant ID provided, only query the maun work
        kwargs['variants_for_work'] = None
        work = Work.objects.get(**kwargs)
        
        #main_work = work
        #if work.variants_for_work is not None:
        #    main_work = work.variants_for_work
    except Exception as (e):
        raise Http404(e)
    
    #return HttpResponse(str(osis_ref_parsed['groups']['start_osis_id']))
    
    
    # TODO: Take into account variant_bit
    
    # Get the structure for the start and end
    start_structure = TokenStructure.objects.select_related(depth=1).get(
        work = work,
        start_token__isnull = False,
        osis_id = osis_ref_parsed['groups']['start_osis_id']
    ) #.extra(where="variant_bits & %s != 0", params=[work.variant_bit])
    #print start_structure
    #return HttpResponse(start_structure)
    #start_structure = start_structure[0]
    
    if osis_ref_parsed['groups']['end_osis_id']:
        end_structure = TokenStructure.objects.select_related(depth=1).get(
            work = work,
            end_token__isnull = False,
            osis_id = osis_ref_parsed['groups']['end_osis_id']
        ) #.extra(where="variant_bits & %s != 0", params=[work.variant_bit])
        #end_structure = end_structure[0]
    else:
        end_structure = start_structure
    
    # Now grab all structures from the work which have start/end_token or
    #  start/end_marker_token whose positions are less 
    
    concurrent_structures = TokenStructure.objects.select_related(depth=1).filter(work = work).filter(
        # Structures that are contained within the start_structure-end_structure span
        (
            (
                Q(start_token__position__lte = start_structure.start_token.position)
                |
                Q(
                    start_marker_token__isnull = False,
                    start_marker_token__position__lte = start_structure.start_token.position
                )
            )
            &
            ( # is this right???
                Q(end_token__position__gte = end_structure.end_token.position)
                |
                Q(
                    end_marker_token__isnull = False,
                    end_marker_token__position__gte = end_structure.end_token.position
                )
            )
        )
        |
        # Structures that start inside of the selected range
        Q(
            start_token__position__gte = start_structure.start_token.position,
            start_token__position__lte = end_structure.end_token.position
        )
        |
        # Structures that end inside of the selected range
        Q(
            end_token__position__gte = start_structure.start_token.position,
            end_token__position__lte = end_structure.end_token.position
        )
        # TODO: What about markers?
    )#.extra(where="variant_bits & %s != 0", params=[work.variant_bit])
    
    # TODO: I need to do two separate queries, or three separate queries?
    
    for struct in concurrent_structures:
        if struct.start_token.position < start_structure.start_token.position:
            struct.shadow = struct.shadow | TokenStructure.SHADOW_START
        if struct.end_token.position > end_structure.end_token.position:
            struct.shadow = struct.shadow | TokenStructure.SHADOW_END
    
    
    #return HttpResponse(len(concurrent_structures))
    
    #print concurrent_structures
    
    #return HttpResponse(str(start_structure.start_token.position) + " - " + str(end_structure.end_token))
    
    # Get all of the structures for a given work including their start_token/end_token
    # Ignore all structures that don't have start_token
    # Then for the tokens that exist the requested structure(s), then query
    # all stuctures that overlap the positions of the start_token and end_token
    

    # Get start and end positions for the tokens
    start_pos = token_start_pos = start_structure.start_token.position
    end_pos   = token_end_pos   = end_structure.end_token.position
    
    # Get start position for marker
    marker_start_pos = token_start_pos
    if start_structure.start_marker_token is not None:
        start_pos = marker_start_pos = start_structure.start_marker_token.position
        assert(marker_start_pos <= token_start_pos)
    
    # Get end position for the marker
    marker_end_pos = token_end_pos
    if end_structure.end_marker_token is not None:
        end_pos = marker_end_pos = end_structure.end_marker_token.position
        assert(marker_end_pos >= token_end_pos)
    
    # Get all of the tokens between the marker start and marker end
    # and who have variant bits that match the requested variant bits
    tokens = Token.objects.filter(
        work = work,
        position__gte = start_pos,
        position__lte = end_pos
    ).extra(where=['variant_bits & %s != 0'], params=[work.variant_bit])
    #if variant_bits is not None:
    #    tokens = tokens.extra(where=['variant_bits & %s != 0'], params=[variant_bits])
    
    # Indicate which of the beginning queried tokens are markers
    for token in tokens:
        if token.position >= token_start_pos:
            break
        token.is_structure_marker = True
    
    # Indicate which of the ending queried tokens are markers
    for token in reversed(tokens):
        if token.position <= token_end_pos:
            break
        token.is_structure_marker = True
    
    
    #tokens = structure.get_tokens()
    return render_to_response('passage_lookup.html', {
        #'osis_id': osis_id,
        'osis_ref_parsed': osis_ref_parsed,
        'start_structure': start_structure,
        'end_structure': end_structure,
        'tokens': tokens,
        'concurrent_structures': concurrent_structures
    })
    

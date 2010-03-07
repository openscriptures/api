# coding: utf8 #

from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.http import Http404
from api.models import *
from django.db.models import Q
from api import osis
import json

def get_osis(request, osis_ref):
    osis_ref_parsed = osis.parse_osis_ref(osis_ref)
    
    #TODO: We should be able to query non-main works as well (i.e. where variants_for_work != None)
    
    try:
        kwargs = osis_ref_parsed['work_prefix']
        #If variant ID provided, only query the main work
        kwargs['variants_for_work'] = None
        work = Work.objects.get(**kwargs)
        
        #main_work = work
        #if work.variants_for_work is not None:
        #    main_work = work.variants_for_work
    except Exception as (e):
        raise Http404(e)
    
    data = work.lookup_osis_ref(
        osis_ref_parsed['groups']['start_osis_id'],
        osis_ref_parsed['groups']['end_osis_id']
    )
    
    if request.GET.has_key("hierarchy"):
        print request.GET["hierarchy"]
    else:
        print "FOOD"    
    
    # 1 A
    # 2 B
    # 3 ¶
    # 4 C
    # 5 D
    
    # hierarchy=book,chapter,verse,paragraph
    # <b>
    #   <c>
    #     <v>
    #        <p sID />
    #        a
    #        b
    #     </v>
    #     <v>
    #        c
    #        d
    #        <p eID />
    #     </v>
    #   </c>
    # </b>
    
    
    # Gather the positions of each structure's bounding tokens
    initialShadowStructures = []
    structuresByTokenStartPosition = {}
    structuresByTokenEndPosition = {}
    terminalShadowStructures = []
    
    for struct in data['concurrent_structures']:
        if struct.start_token.position < data['start_structure'].start_token.position:
            initialShadowStructures.append(struct)
        
        if not structuresByTokenStartPosition.has_key(struct.start_token.position):
            structuresByTokenStartPosition[struct.start_token.position] = []
        structuresByTokenStartPosition[struct.start_token.position].append(struct)
        
        if not structuresByTokenEndPosition.has_key(struct.end_token.position):
            structuresByTokenEndPosition[struct.end_token.position] = []
        structuresByTokenEndPosition[struct.end_token.position].append(struct)
        
        if struct.end_token.position > data['end_structure'].end_token.position:
            terminalShadowStructures.append(struct)
    
    # Now sort each array in structuresByTokenStartPosition and
    # structuresByTokenEndPosition by GET['hierarchy'] and indicate for each
    # whether it is_milestoned
    # QUESTION: The objects are stored by reference, so if is_milestoned is set
    #           in one it will be set in the other, correct?
    
    print initialShadowStructures
    print terminalShadowStructures
    
    
    # TODO: It is important that the structures be sorted either by their
    #       inherent size, or by their actual size, so that structures that span
    #       more tokens will wrap structures that contain fewer
    #       We need to sort the structures by the order that we want them to appear in
    
    passage = ""
    
    def handleStructure(struct, isShadow, isStart):
        text = "["
        if not isStart:
            text += "/"
        if struct.type == TokenStructure.BOOK:
            text += "BOOK"
        if struct.type == TokenStructure.CHAPTER:
            text += "CHAPTER"
        if struct.type == TokenStructure.VERSE:
            text += "VERSE"
        if struct.type == TokenStructure.PARAGRAPH:
            text += "P"
        if isShadow:
            text += " shadow"
        text += "]"
        return text
    
    for struct in initialShadowStructures:
        passage += handleStructure(struct, True, True)
    
    
    
    for token in data['tokens']:
        #TODO: Should we close the end tokens and then open the start?
        if structuresByTokenEndPosition.has_key(token.position):
            for struct in reversed(structuresByTokenEndPosition[token.position]):
                passage += handleStructure(struct, False, False)
        
        if structuresByTokenStartPosition.has_key(token.position):
            for struct in structuresByTokenStartPosition[token.position]:
                passage += handleStructure(struct, False, True)
        
        passage += token.data
    
    for struct in reversed(terminalShadowStructures):
        passage += handleStructure(struct, True, False)
    
    #data['concurrent_structures']
    
    
    # data['tokens']
    # data['concurrent_structures']
    
    
    
    return render_to_response('passage_lookup.html', {
        'osis_ref':osis_ref,
        'osis_ref_parsed': osis_ref_parsed,
        'start_structure': data['start_structure'],
        'end_structure': data['end_structure'],
        'tokens': data['tokens'],
        'concurrent_structures': data['concurrent_structures'],
        'passage': passage
    })
    

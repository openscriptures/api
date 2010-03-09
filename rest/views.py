# coding: utf8 #

from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.http import *
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
    
    
    # Get the desired hierarchy (serialization order) for TokenStructures
    structureTypes = []
    structureTypeLookup = {}
    structureTypeHierarchy = []
    for choice_tuple in TokenStructure.TYPES_CHOICES:
        structureTypeLookup[choice_tuple[1]] = choice_tuple[0]
        structureTypes.append(choice_tuple[0])
    if request.GET.has_key("hierarchy"):
        # Gather the structures specified in the qeury
        for structType in request.GET["hierarchy"].split(","):
            if not structureTypeLookup.has_key(structType):
                return HttpResponseBadRequest("Unexpected structure type '%s' provided for hieararchy" % structType) #TODO: This needs to be escaped
            structureTypeHierarchy.append(structureTypeLookup[structType])
        
        # Append any remaining
        for structType in structureTypes:
            if structType not in structureTypeHierarchy:
                structureTypeHierarchy.append(structType)
    else: #default order
        structureTypeHierarchy = structureTypes
        
    
    # Gather the positions of each structure's bounding tokens
    initialShadowStructures = []
    structuresByTokenStartPosition = {}
    structuresByTokenEndPosition = {}
    finalShadowStructures = []
    
    for struct in data['concurrent_structures']:
        if struct.start_token.position < data['start_structure'].start_token.position:
            struct.shadow = struct.shadow | TokenStructure.SHADOW_START
            initialShadowStructures.append(struct)
        
        if struct.end_token.position > data['end_structure'].end_token.position:
            struct.shadow = struct.shadow | TokenStructure.SHADOW_END
            finalShadowStructures.append(struct)
        
        if not structuresByTokenStartPosition.has_key(struct.start_token.position):
            structuresByTokenStartPosition[struct.start_token.position] = []
        structuresByTokenStartPosition[struct.start_token.position].append(struct)
        
        if not structuresByTokenEndPosition.has_key(struct.end_token.position):
            structuresByTokenEndPosition[struct.end_token.position] = []
        structuresByTokenEndPosition[struct.end_token.position].append(struct)
    
    # Stick initialShadowStructures and finalShadowStructures onto the first
    # token and last token's respective structure lists
    if len(initialShadowStructures):
        pos = data['tokens'][0].position
        if not structuresByTokenStartPosition.has_key(pos):
            structuresByTokenStartPosition[pos] = []
        for struct in initialShadowStructures:
            structuresByTokenStartPosition[pos].append(struct)
    if len(finalShadowStructures):
        pos = data['tokens'][len(data['tokens'])-1].position
        if not structuresByTokenEndPosition.has_key(pos):
            structuresByTokenEndPosition[pos] = []
        for struct in finalShadowStructures:
            structuresByTokenEndPosition[pos].append(struct)
    
    
    # Now sort each array in structuresByTokenStartPosition and
    # structuresByTokenEndPosition by GET['hierarchy'] and indicate for each
    # whether it is_milestoned
    def sorter(a, b):
        return cmp(
            structureTypeHierarchy.index(a.type),
            structureTypeHierarchy.index(b.type)
        )
    
    for structureGroup in (structuresByTokenStartPosition, structuresByTokenEndPosition):
        for structs in structureGroup.values():
            if len(structs):
                structs.sort(sorter)
                # Detect overlapping hierarchies (and need for milestones)
                structs[0].is_milestoned |= False
                max_start_position = structs[0].start_token.position
                min_end_position = structs[0].end_token.position
                for i in range(1, len(structs)):
                    # Start
                    if structs[i].start_token.position < max_start_position:
                       structs[i].is_milestoned = True
                    else:
                       max_start_position = structs[i].start_token.position
                    
                    # End
                    if structs[i].end_token.position > min_end_position:
                       structs[i].is_milestoned = True
                    else:
                       min_end_position = structs[i].end_token.position
    
    
    # TODO: It is important that the structures be sorted either by their
    #       inherent size, or by their actual size, so that structures that span
    #       more tokens will wrap structures that contain fewer
    #       We need to sort the structures by the order that we want them to appear in
    
    passage = ""
    
    #TODO: This should instead return an object for the view to process, including whether it is milestone
    def handleStructure(struct, isStart):
        if struct.type == TokenStructure.BOOK:
            elName = "book"
        elif struct.type == TokenStructure.CHAPTER:
            elName = "chapter"
        if struct.type == TokenStructure.VERSE:
            elName = "verse"
        if struct.type == TokenStructure.PARAGRAPH:
            elName = "p"
        
        shadow = ""
        if struct.shadow:
            if struct.shadow == TokenStructure.SHADOW_START:
                shadow = "start"
            elif struct.shadow == TokenStructure.SHADOW_END:
                shadow = "end"
            elif struct.shadow == TokenStructure.SHADOW_BOTH:
                shadow = "both"
            else:
                shadow = "none"
        
        ret = ""
        if struct.is_milestoned:
            ret += "<" + elName
            if isStart:
                if shadow:
                    ret += " shadow='" + shadow + "'"
                ret += " sID='" + str(struct.id) + "'"
            else:
                ret += " eID='" + str(struct.id) + "'"
            ret += " />"
        else:
            if isStart:
                ret += "<" + elName
                if shadow:
                    ret += " shadow='" + shadow + "'"
                ret += ">"
            else:
                ret += "</" + elName + ">"
        return ret
    
    
    
    for token in data['tokens']:
        if structuresByTokenStartPosition.has_key(token.position):
            for struct in structuresByTokenStartPosition[token.position]:
                passage += handleStructure(struct, True)
        
        passage += token.data
        
        #TODO: Should we close the end tokens and then open the start?
        #      NO: Because there must be no overlap
        if structuresByTokenEndPosition.has_key(token.position):
            #assert(not structuresByTokenStartPosition.has_key(token.position)) #Ensure no overlap?
            for struct in reversed(structuresByTokenEndPosition[token.position]):
                passage += handleStructure(struct, False)
    
    
    
    return render_to_response('passage_lookup.html', {
        'osis_ref':osis_ref,
        'osis_ref_parsed': osis_ref_parsed,
        'start_structure': data['start_structure'],
        'end_structure': data['end_structure'],
        'tokens': data['tokens'],
        'concurrent_structures': data['concurrent_structures'],
        'passage': passage
    })
    

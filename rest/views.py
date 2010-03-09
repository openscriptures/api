# coding: utf8 #

from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.http import *
from api.models import *
from django.db.models import Q
from api import osis
import json

def get_passage(request, osis_ref):
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
    structureTypesAlwaysMilestoned = {}
    structureTypeLookup = {}
    structureTypeHierarchy = []
    for choice_tuple in TokenStructure.TYPES_CHOICES:
        structureTypeLookup[choice_tuple[1]] = choice_tuple[0]
        structureTypes.append(choice_tuple[0])
    if request.GET.has_key("hierarchy"):
        # Gather the structures specified in the qeury
        for structType in request.GET["hierarchy"].split(","):
            always_milestone = structType.startswith('~')
            if always_milestone:
                structType = structType[1:]
                structureTypesAlwaysMilestoned[structureTypeLookup[structType]] = True
            
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
    passage_start_token_position = data['tokens'][0].position
    if len(initialShadowStructures):
        if not structuresByTokenStartPosition.has_key(passage_start_token_position):
            structuresByTokenStartPosition[passage_start_token_position] = []
        for struct in initialShadowStructures:
            structuresByTokenStartPosition[passage_start_token_position].append(struct)
    passage_end_token_position = data['tokens'][len(data['tokens'])-1].position
    if len(finalShadowStructures):
        if not structuresByTokenEndPosition.has_key(passage_end_token_position):
            structuresByTokenEndPosition[passage_end_token_position] = []
        for struct in finalShadowStructures:
            structuresByTokenEndPosition[passage_end_token_position].append(struct)
    
    # Now sort each array in structuresByTokenStartPosition and
    # structuresByTokenEndPosition by the requested hierarchy and indicate for
    # each whether it is_milestoned
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
                # TODO: What if the first struct is desired to be milestoned?
                structs[0].is_milestoned |= False
                max_start_position = max(structs[0].start_token.position, passage_start_token_position)
                min_end_position = min(structs[0].end_token.position, passage_end_token_position)
                for i in range(1, len(structs)):
                    # Always milestone
                    if structureTypesAlwaysMilestoned.has_key(structs[i].type):
                        structs[i].is_milestoned = True
                        continue
                    
                    start_position = max(structs[i].start_token.position, max_start_position)
                    end_position = min(structs[i].end_token.position, min_end_position)
                    
                    # Check for needing start milestone
                    if max(structs[i].start_token.position, passage_start_token_position) < start_position:
                        structs[i].is_milestoned = True
                    else:
                        max_start_position = start_position
                    
                    # Check for needing end milestone
                    if min(structs[i].end_token.position, passage_end_token_position) > end_position:
                        structs[i].is_milestoned = True
                    else:
                        min_end_position = end_position
    
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
                if struct.osis_id:
                    ret += " osisID='" + struct.osis_id + "'"
                if shadow:
                    ret += " shadow='" + shadow + "'"
                ret += " sID='" + str(struct.id) + "'"
            else:
                ret += " eID='" + str(struct.id) + "'"
            ret += " />"
        else:
            if isStart:
                ret += "<" + elName
                ret += " osisID='" + struct.osis_id + "'"
                if shadow:
                    ret += " shadow='" + shadow + "'"
                ret += ">"
            else:
                ret += "</" + elName + ">"
        return ret
    
    
    # TODO: Output here should be streamed to the template
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
    

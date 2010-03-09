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
    
    #print structureTypeHierarchy
    
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
    
    # Now sort each array in structuresByTokenStartPosition and
    # structuresByTokenEndPosition by GET['hierarchy'] and indicate for each
    # whether it is_milestoned
    def sorter(a, b):
        return cmp(
            structureTypeHierarchy.index(a.type),
            structureTypeHierarchy.index(b.type)
        )
    
    initialShadowStructures.sort(sorter)
    finalShadowStructures.sort(sorter)
    for structureGroup in (structuresByTokenStartPosition, structuresByTokenEndPosition):
        print
        for structs in structureGroup.values():
            print "group at: " + structs[0].start_token.data
            if len(structs):
                structs.sort(sorter)
                # Detect overlapping hierarchies (and need for milestones)
                structs[0].is_milestoned |= False
                max_start_position = structs[0].start_token.position
                min_end_position = structs[0].end_token.position
                print " - " + str(structs[0]) + " " + str(structs[0].is_milestoned) + " " + str(structs[0].shadow)
                for i in range(1, len(structs)):
                    if structs[i].start_token.position < max_start_position:
                       structs[i].is_milestoned = True
                    else:
                       max_start_position = structs[i].start_token.position
                    
                    if structs[i].end_token.position > min_end_position:
                       structs[i].is_milestoned = True
                    else:
                       min_end_position = structs[i].end_token.position
                    print " - " + str(structs[i]) + " " + str(structs[i].is_milestoned) + " " + str(structs[i].shadow)
        
    #for structs in structuresByTokenEndPosition.values():
    #    if len(structs):
    #        structs.sort(sorter)
    #        # Detect overlapping hierarchies (and need for milestones)
    #        structs[0].is_milestoned = False
    #        min_start_position = structs[0].start_token.position
    #        max_end_position = structs[0].end_token.position
    #        for i in range(1, len(structs)):
    #            print str(structs[i]) + " " + str(structs[i].is_milestoned)
    #            if structs[i].start_token.position < min_start_position:
    #               structs[i].is_milestoned = True
    #               min_start_position = structs[i].start_token.position
    #            if structs[i].end_token.position > max_end_position:
    #               structs[i].is_milestoned = True
    #               max_end_position = structs[i].end_token.position
    
    
    
    # TODO: It is important that the structures be sorted either by their
    #       inherent size, or by their actual size, so that structures that span
    #       more tokens will wrap structures that contain fewer
    #       We need to sort the structures by the order that we want them to appear in
    
    passage = ""
    
    #TODO: This should instead return an object for the view to process, including whether it is milestone
    def handleStructure(struct, isStart):
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
        if struct.shadow:
            text += " shadow='"
            if struct.shadow == TokenStructure.SHADOW_START:
                text += "start"
            elif struct.shadow == TokenStructure.SHADOW_END:
                text += "end"
            elif struct.shadow == TokenStructure.SHADOW_BOTH:
                text += "both"
            else:
                text += "none"
            text += "'"
        text += "]"
        text += str(isStart)
        return text
    
    # TODO: initialShadowStructures needs to be merged into the start token
    for struct in initialShadowStructures:
        passage += handleStructure(struct, 'blast')
    
    
    
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
    
    for struct in reversed(finalShadowStructures):
        passage += handleStructure(struct, False)
    
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
    

# coding: utf8 #

from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.http import *
from api.models import *
from django.db.models import Q
from api import osis
import json

def passage(request, osis_ref):
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
    
    # TODO: This is too simplistic; we have more complex passage slugs that we want to support
    data = work.lookup_osis_ref(
        osis_ref_parsed['groups']['start_osis_id'],
        osis_ref_parsed['groups']['end_osis_id']
    )
    
    # Get the output format
    output_formats = {
        'debug':{
            'template_name':'passage_debug.html',
            'mimetype': 'text/html'
        },
        'xml':{
            'template_name':'passage.xml',
            'mimetype': 'application/xml'
        }
    }
    output_format = "xml"
    
    
    # Get the desired hierarchy (serialization order) for TokenStructures
    structure_types = []
    structure_types_always_milestoned = {}
    structure_type_name2code = {}
    structure_type_code2name = {}
    structure_type_hierarchy = []
    for choice_tuple in TokenStructure.TYPES_CHOICES: #TODO: There's gotta be a better way to do reverse lookup of choices tuples
        structure_type_name2code[choice_tuple[1]] = choice_tuple[0]
        structure_type_code2name[choice_tuple[0]] = choice_tuple[1]
        structure_types.append(choice_tuple[0])
    if request.GET.has_key("hierarchy"):
        # Predefined hierarchy: Book-Chapter-Verse
        if request.GET["hierarchy"] == 'bcv':
            structure_type_hierarchy = ["bookGroup", "book", "chapter", "verse"]
        
        # Predefined hierarchy: Book-Section-Paragraph
        elif request.GET["hierarchy"] == 'bsp':
            structure_type_hierarchy = ["bookGroup", "book", "section", "paragraph", "line"]
            structure_types_always_milestoned[TokenStructure.VERSE] = True
            structure_types_always_milestoned[TokenStructure.CHAPTER] = True
        
        # Custom hierarchy specified in request
        else:
            for struct_type in request.GET["hierarchy"].split(","):
                always_milestone = struct_type.startswith('~')
                if always_milestone:
                    struct_type = struct_type[1:]
                    structure_types_always_milestoned[structure_type_name2code[struct_type]] = True
                
                if not structure_type_name2code.has_key(struct_type):
                    return HttpResponseBadRequest("Unexpected structure type '%s' provided for hieararchy" % struct_type) #TODO: This needs to be escaped
                structure_type_hierarchy.append(structure_type_name2code[struct_type])
        
        # Append any remaining in the order they are defined
        for struct_type in structure_types:
            if struct_type not in structure_type_hierarchy:
                structure_type_hierarchy.append(struct_type)
    else: #default order
        structure_type_hierarchy = structure_types
        
    
    # Gather the positions of each structure's bounding tokens and the
    # structures that start and end at each token
    initial_shadow_structures = []
    structures_by_token_start_position = {}
    structures_by_token_end_position = {}
    final_shadow_structures = []
    for struct in data['concurrent_structures']:
        if struct.start_token.position < data['start_structure'].start_token.position:
            struct.shadow = struct.shadow | TokenStructure.SHADOW_START
            initial_shadow_structures.append(struct)
        
        if struct.end_token.position > data['end_structure'].end_token.position:
            struct.shadow = struct.shadow | TokenStructure.SHADOW_END
            final_shadow_structures.append(struct)
        
        if not structures_by_token_start_position.has_key(struct.start_token.position):
            structures_by_token_start_position[struct.start_token.position] = []
        structures_by_token_start_position[struct.start_token.position].append(struct)
        
        if not structures_by_token_end_position.has_key(struct.end_token.position):
            structures_by_token_end_position[struct.end_token.position] = []
        structures_by_token_end_position[struct.end_token.position].append(struct)
    
    # Stick initial_shadow_structures and final_shadow_structures onto the first
    # token and last token's respective structure lists
    passage_start_token_position = data['tokens'][0].position
    if len(initial_shadow_structures):
        if not structures_by_token_start_position.has_key(passage_start_token_position):
            structures_by_token_start_position[passage_start_token_position] = []
        for struct in initial_shadow_structures:
            structures_by_token_start_position[passage_start_token_position].append(struct)
    passage_end_token_position = data['tokens'][len(data['tokens'])-1].position
    if len(final_shadow_structures):
        if not structures_by_token_end_position.has_key(passage_end_token_position):
            structures_by_token_end_position[passage_end_token_position] = []
        for struct in final_shadow_structures:
            structures_by_token_end_position[passage_end_token_position].append(struct)
    
    # Now sort each array in structures_by_token_start_position and
    # structures_by_token_end_position by the requested hierarchy and indicate for
    # each whether it is_milestoned
    def sorter(a, b):
        return cmp(
            structure_type_hierarchy.index(a.type),
            structure_type_hierarchy.index(b.type)
        )
    
    for structure_group in (structures_by_token_start_position, structures_by_token_end_position):
        for structs in structure_group.values():
            if len(structs):
                structs.sort(sorter)
                # Detect overlapping hierarchies (and need for milestones)
                # TODO: What if the first struct is desired to be milestoned?
                structs[0].is_milestoned |= False
                max_start_position = max(structs[0].start_token.position, passage_start_token_position)
                min_end_position = min(structs[0].end_token.position, passage_end_token_position)
                for i in range(1, len(structs)):
                    # Always milestone
                    if structure_types_always_milestoned.has_key(structs[i].type):
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
    def temp_handle_structure(struct, isStart):
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
                if struct.osis_id:
                    ret += " osisID='" + struct.osis_id + "'"
                if shadow:
                    ret += " shadow='" + shadow + "'"
                ret += ">"
            else:
                ret += "</" + elName + ">"
        return ret
    
    # How do I pass in constructor arguments?
    #class PassageChunk():
    #    is_structure = None
    #    is_token = None
    #    shadow = None
    #    object = None
        
    passage_chunks = []
    
    # TODO: Output here should be streamed to the template
    for token in data['tokens']:
        if structures_by_token_start_position.has_key(token.position):
            for struct in structures_by_token_start_position[token.position]:
                passage_chunks.append({
                    'is_structure': True,
                    'is_start': True,
                    'structure': struct,
                    'type': structure_type_code2name[struct.type]
                })
                #passage += temp_handle_structure(struct, True)
        
        #passage += token.data
        passage_chunks.append({
            'is_token': True,
            'token': token
        })
        
        if structures_by_token_end_position.has_key(token.position):
            for struct in reversed(structures_by_token_end_position[token.position]):
                passage_chunks.append({
                    'is_structure': True,
                    'is_end': True,
                    'structure': struct,
                    'type': structure_type_code2name[struct.type]
                })
                #passage += temp_handle_structure(struct, False)
    
    
    template_vars = {
        'passages':[]
    }
    
    template_vars['passages'].append({
        'osis_ref': osis_ref,
        #'osis_ref_parsed': osis_ref_parsed,
        'start_structure': data['start_structure'],
        'end_structure': data['end_structure'],
        'tokens': data['tokens'],
        'concurrent_structures': data['concurrent_structures'],
        'chunks':passage_chunks
    })
    
    
    # TODO: We need to select the template based on the requested outout
    return render_to_response(
        output_formats[output_format]['template_name'],
        template_vars,
        mimetype=output_formats[output_format]['mimetype']
    )
    
    #context_instance=RequestContext(request) ???
    

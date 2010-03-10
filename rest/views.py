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
    STRUCTURE_TYPE_CODES = {}
    structure_type_hierarchy = []
    for choice_tuple in TokenStructure.TYPE_CHOICES: #TODO: There's gotta be a better way to do reverse lookup of choices tuples
        STRUCTURE_TYPE_CODES[choice_tuple[1]] = choice_tuple[0]
        structure_types.append(choice_tuple[0])
    
    
    if request.GET.has_key("hierarchy"):
        if request.GET["hierarchy"] == 'standoff':
            is_standoff = True
        else:
            is_standoff = False
            
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
                        structure_types_always_milestoned[STRUCTURE_TYPE_CODES[struct_type]] = True
                    
                    if not STRUCTURE_TYPE_CODES.has_key(struct_type):
                        return HttpResponseBadRequest("Unexpected structure type '%s' provided for hieararchy" % struct_type) #TODO: This needs to be escaped
                    structure_type_hierarchy.append(STRUCTURE_TYPE_CODES[struct_type])
            
            # Append any remaining in the order they are defined
            for struct_type in structure_types:
                if struct_type not in structure_type_hierarchy:
                    structure_type_hierarchy.append(struct_type)
    else: #default order
        structure_type_hierarchy = structure_types
    
    passage_start_token_position = data['tokens'][0].position
    passage_end_token_position = data['tokens'][len(data['tokens'])-1].position
    
    # Gather the positions of each structure's bounding tokens and the
    # structures that start and end at each token
    initial_shadow_structures = []
    structures_by_token_start_position = {}
    structures_by_token_end_position = {}
    final_shadow_structures = []
    for struct in data['concurrent_structures']:
        # Structure is start shadow
        if struct.start_token.position < data['start_structure'].start_token.position:
            struct.shadow = struct.shadow | TokenStructure.SHADOW_START
            initial_shadow_structures.append(struct)
            struct.shadow_start_token_position = passage_start_token_position
        
        if not structures_by_token_start_position.has_key(struct.start_token.position):
            structures_by_token_start_position[struct.start_token.position] = []
        structures_by_token_start_position[struct.start_token.position].append(struct)
        
        # Structure is end shadow
        if struct.end_token.position > data['end_structure'].end_token.position:
            struct.shadow = struct.shadow | TokenStructure.SHADOW_END
            final_shadow_structures.append(struct)
            struct.shadow_end_token_position = passage_end_token_position
        
        if not structures_by_token_end_position.has_key(struct.end_token.position):
            structures_by_token_end_position[struct.end_token.position] = []
        structures_by_token_end_position[struct.end_token.position].append(struct)
    
    # Stick initial_shadow_structures and final_shadow_structures onto the first
    # token and last token's respective structure lists
    if len(initial_shadow_structures):
        if not structures_by_token_start_position.has_key(passage_start_token_position):
            structures_by_token_start_position[passage_start_token_position] = []
        for struct in initial_shadow_structures:
            structures_by_token_start_position[passage_start_token_position].append(struct)
    if len(final_shadow_structures):
        if not structures_by_token_end_position.has_key(passage_end_token_position):
            structures_by_token_end_position[passage_end_token_position] = []
        for struct in final_shadow_structures:
            structures_by_token_end_position[passage_end_token_position].append(struct)
    
        
    passage_chunks = []
    
    if not is_standoff:

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
        
        # Iterate over all of the tokens and turn them and the structures associated
        # with them into “chunks” for the template to render
        for token in data['tokens']:
            if structures_by_token_start_position.has_key(token.position):
                for struct in structures_by_token_start_position[token.position]:
                    passage_chunks.append({
                        'is_start': True,
                        'structure': struct
                    })
            
            passage_chunks.append({
                'token': token
            })
            
            if structures_by_token_end_position.has_key(token.position):
                for struct in reversed(structures_by_token_end_position[token.position]):
                    passage_chunks.append({
                        'is_end': True,
                        'structure': struct
                    })
    
    
    template_vars = {
        'passages':[]
    }
    
    passage = {
        'is_standoff':is_standoff,
        'osis_ref': osis_ref,
        #'osis_ref_parsed': osis_ref_parsed,
        'start_structure': data['start_structure'],
        'end_structure': data['end_structure'],
        'tokens': data['tokens'],
        'structures': data['concurrent_structures'],
        'chunks':passage_chunks
    }
    
    template_vars['passages'].append(passage)
    
    
    # TODO: We need to select the template based on the requested outout
    return render_to_response(
        output_formats[output_format]['template_name'],
        template_vars,
        mimetype=output_formats[output_format]['mimetype']
    )
    
    #context_instance=RequestContext(request) ???
    

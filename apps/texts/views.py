# coding: utf8 #

from django.http import Http404, HttpResponseBadRequest
from django.shortcuts import render_to_response

from texts.models import Work, Structure
from core.osis import OsisRef



def passage(request, osis_ref):
    osis_ref = OsisRef(osis_ref)
    
    #TODO: We should be able to query non-main works as well (i.e. where variants_for_work != None)
    
    try:
        # This needs a lot of improvements
        # TODO: osis_slug is used in DB model, but 'name' is used by osis.py;
        # TODO: make Work.objects.getByOsisWork()
        work_dict_query = {}
        for key in ('publisher', 'language', 'publish_date', 'type'):
            if osis_ref.work.__dict__[key] is not None:
                work_dict_query[key] = osis_ref.work.__dict__[key]
        if 'name' in osis_ref.work.__dict__: # 
            work_dict_query['osis_slug'] = osis_ref.work.__dict__['name']
        work = Work.objects.get(**work_dict_query)
        
        #main_work = work
        #if work.variants_for_work is not None:
        #    main_work = work.variants_for_work
    except Exception as (e):
        raise Http404(e)
    
    # TODO: This is too simplistic; we have more complex passage slugs that we want to support
    data = work.lookup_osis_ref(
        str(osis_ref.start),
        str(osis_ref.end),
    )
    
    # Define the output formats and their templates
    output_formats = {
        #'debug':{
        #    'template_name':'passage_debug.html',
        #    'mimetype': 'text/html'
        #},
        'xml':{
            'template_name':'passage.xml',
            'mimetype': 'application/xml',
            'standoff_allowed': True
        },
        'xhtml':{
            'template_name':'passage.xhtml',
            'mimetype': 'application/xhtml+xml',
            'standoff_allowed': False
        }
    }
    
    # Get the output format
    output_format = "xml" #default
    if request.GET.has_key("output"):
        if not output_formats.has_key(request.GET["output"]):
            return HttpResponseBadRequest("Unexpected output type '%s' provided for hierarchy" % request.GET["output"], mimetype = "text/plain")
        output_format = request.GET["output"]
    
    # Get the desired hierarchy (serialization order) for Structures
    structure_types = []
    structure_types_always_milestoned = {}
    #STRUCTURE_TYPE_CODES = {}
    structure_type_hierarchy = []
    #for choice_tuple in Structure.TYPE_CHOICES: #TODO: There's gotta be a better way to do reverse lookup of choices tuples
    #    STRUCTURE_TYPE_CODES[choice_tuple[1]] = choice_tuple[0]
    #    structure_types.append(choice_tuple[0])
    
    
    is_standoff = False
    if request.GET.has_key("hierarchy"):
        if request.GET["hierarchy"] == 'standoff':
            is_standoff = True
            assert(output_formats[output_format]['standoff_allowed'])
        else:
            is_standoff = False
            
            # Predefined hierarchy: Book-Chapter-Verse
            if request.GET["hierarchy"] == 'bcv':
                structure_type_hierarchy = [
                    'bookGroup',
                    'book',
                    'chapter',
                    'verse',
                ]
                structure_types_always_milestoned['p'] = True
            
            # Predefined hierarchy: Book-Section-Paragraph
            elif request.GET["hierarchy"] == 'bsp':
                structure_type_hierarchy = [
                    'bookGroup',
                    'book',
                    'section',
                    'p',
                    'l'
                ]
                structure_types_always_milestoned['verse'] = True
                structure_types_always_milestoned['chapter'] = True
            
            # Predefined hierarchy: Book-Section-Paragraph
            elif request.GET["hierarchy"] == 'milestone':
                for struct_type in structure_types:
                    structure_types_always_milestoned[struct_type] = True
            
            # Custom hierarchy specified in request
            else:
                for struct_type in request.GET["hierarchy"].split(","):
                    always_milestone = struct_type.startswith('~')
                    if always_milestone:
                        struct_type = struct_type[1:]
                        structure_types_always_milestoned[struct_type] = True
                    
                    #if not STRUCTURE_TYPE_CODES.has_key(struct_type):
                    #    return HttpResponseBadRequest("Unexpected structure type '%s' provided for hieararchy" % struct_type, mimetype = "text/plain")
                    structure_type_hierarchy.append(struct_type)
            
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
            struct.shadow = struct.shadow | Structure.SHADOW_START
            initial_shadow_structures.append(struct)
            struct.shadow_start_token_position = passage_start_token_position
        
        if not structures_by_token_start_position.has_key(struct.start_token.position):
            structures_by_token_start_position[struct.start_token.position] = []
        structures_by_token_start_position[struct.start_token.position].append(struct)
        
        # Structure is end shadow
        if struct.end_token.position > data['end_structure'].end_token.position:
            struct.shadow = struct.shadow | Structure.SHADOW_END
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
                    max_start_position = max(structs[0].start_token.position, passage_start_token_position)
                    min_end_position = min(structs[0].end_token.position, passage_end_token_position)
                    for i in range(0, len(structs)):
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
    
    #TODO: Allow multiple passages to be queried at once
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
    

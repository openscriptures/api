# coding: utf8 #

from django.db import models
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _

from core.models import Language, License, Server




class WorkServer(models.Model):
    """
    Intermediary table for ManyToMany relationship between Work and Server
    """

    is_primary = models.BooleanField(_("Whether the server is canonical (primary) or not (mirror)"))
    work = models.ForeignKey('Work')
    server = models.ForeignKey(Server)


#TODO: Should we have a WorkProperty model which allows arbitrary key/value pairs?

class Work(models.Model):
    """
    Represents an OSIS work, such as the Bible or a non-biblical work such as
    the Qur'an or the Mishnah.
    """

    title = models.CharField(max_length=255)
    abbreviation = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    source_url = models.URLField(_("URL where this resource was originally obtained"), blank=True)

    #variants_for_work = models.ForeignKey("self", null=True, default=None, verbose_name=_("Parent work that this work provides variants for"))
    #variant_bit = models.PositiveSmallIntegerField(_("The bit mask that is anded with Token.variant_bits and Structure.variant_bits to query only those which belong to the work."), default=0b00000001)

    #TODO: Allow multiple kinds of identifiers for the work:
    #      Including ISBN, URL, URN, in addition to OSIS. OSIS needs to be unique,
    #      and its parts should be deconstructable.

    #Bible.en.Publisher.ABC.2010
    #TODO: this should be pulled from osis.TYPES
    TYPES = (
        ('Bible', 'Bible'),
    )
    #TODO: use short_name?
    osis_slug = models.SlugField(_("OSIS identifier which should correspond to the abbreviation, like NIV, ESV, or KJV"), max_length=16, db_index=True)
    type = models.CharField(max_length=16, choices=TYPES, null=False, db_index=True)
    language = models.ForeignKey(Language, null=True, db_index=True)
    #Note: In the case of Daniel, both Hebrew and Aramaic in the book, though
    #      Hebrew is predominat; in this case, Work.language would still be 'hbo'; the
    #      language of the individual Tokens in the work can be indicated in a
    #      separate TokenMetadata model. This would allow multiple languages to be
    #      associated with a Token as there may be different opinions about what
    #      language it is!


    #TODO: Better way to do attribution for various roles like creator, contributor, publisher in ManyToMany relation
    #      (Also need slugs for the URL)
    publisher = models.CharField(blank=True, max_length=128, db_index=True)
    creator = models.TextField(blank=True)

    #TODO: Better system for storing multiple dates for a work, e.g. OSIS
    #      date tlements: edition, eversion, imprint, original
    publish_date = models.DateField(_("When the work was published"), null=True, db_index=True)
    import_date = models.DateField(_("When the work was imported into the models."), null=True)

    #TODO: pub_date instead?
    #edition
    #version

    #Concatenation of previous fields:
    #osis_id = models.CharField(max_length=32, choices=TYPES, null=False, db_index=True)
    #def get_osis_id(self):
    #    _osis_id = []
    #    if self.type:
    #        _osis_id.append(self.type)
    #    if self.language:
    #        _osis_id.append(self.language.code)
    #    if self.osis_slug:
    #        _osis_id.append(self.osis_slug)
    #    if self.publish_date:
    #        _osis_id.append(self.publish_date.year)
    #    return ".".join(_osis_id)
    #osis_id = property(get_osis_id)

    copyright = models.TextField(blank=True)
    license = models.ForeignKey(License, null=True)

    servers = models.ManyToManyField(Server, through=WorkServer)


    def lookup_osis_ref(self, start_osis_id, end_osis_id = None, variant_bits = None):
        if not end_osis_id:
            end_osis_id = start_osis_id

        # Token and Structure objects are only associated with non-diff
        #   works, that is where variants_for_work is None
        main_work = self
        #if self.variants_for_work is not None:
        #    main_work = self.variants_for_work

        # Allow the variant_bits to be customized to include structures and
        #   tokens from other variants of this work
        #if variant_bits is None:
        #    variant_bits = self.variant_bit

        # Get the structure for the start
        structures = Structure.objects.select_related(depth=1).filter(
            work = main_work,
            start_token__isnull = False,
            osis_id = start_osis_id
        ) #.extra(where=["variant_bits & %s != 0"], params=[variant_bits])
        if len(structures) == 0:
            raise Exception("Start structure with osisID %s not found" % start_osis_id)
        start_structure = structures[0]

        # Get the structure for the end
        if start_osis_id != end_osis_id:
            structures = Structure.objects.select_related(depth=1).filter(
                work = main_work,
                end_token__isnull = False,
                osis_id = end_osis_id
            ) #.extra(where=["variant_bits & %s != 0"], params=[variant_bits])
            if len(structures) == 0:
                raise Exception("End structure with osisID %s not found" % end_osis_id)
            end_structure = structures[0]
        else:
            end_structure = start_structure

        # Now grab all structures from the work which have start/end_token or
        #  start/end_marker whose positions are less 
        concurrent_structures = Structure.objects.select_related(depth=1).filter(work = main_work).filter(
            # Structures that are contained within start_structure and end_structure
            (
                Q(start_token__position__lte = start_structure.start_token.position)
                &
                Q(end_token__position__gte = end_structure.end_token.position)
            )
            |
            # Structures that only start inside of the selected range
            Q(
                start_token__position__gte = start_structure.start_token.position,
                start_token__position__lte = end_structure.end_token.position
            )
            |
            # Structures that only end inside of the selected range (excluding markers)
            Q(
                end_token__position__gte = start_structure.start_token.position,
                end_token__position__lte = end_structure.end_token.position
            )
        ) #.extra(where=["%s.variant_bits & %%s != 0" % Structure._meta.db_table], params=[variant_bits])

        # Now indicate if the structures are shadowed (virtual)
        for struct in concurrent_structures:
            if struct.start_token.position < start_structure.start_token.position:
                struct.shadow = struct.shadow | Structure.SHADOW_START
            if struct.end_token.position > end_structure.end_token.position:
                struct.shadow = struct.shadow | Structure.SHADOW_END

        # Now get all tokens that exist between the beginning of start_structure
        # and the end of end_structure

        # Get all of the tokens between the start and end and who have variant
        # bits that match the requested variant bits
        tokens = Token.objects.filter(
            work = main_work,
            position__gte = start_structure.start_token.position,
            position__lte = end_structure.end_token.position
        ) #.extra(where=['variant_bits & %s != 0'], params=[variant_bits])

        # Indicate which of the beginning queried tokens are markers (should be none since verse)
        for token in tokens:
            if token.position >= start_structure.start_token.position:
                break
            token.is_structure_marker = True

        # Indicate which of the ending queried tokens are markers (should be none since verse)
        for token in reversed(tokens):
            if token.position <= end_structure.end_token.position:
                break
            token.is_structure_marker = True

        return {
            'start_structure': start_structure,
            'end_structure': end_structure,
            'tokens': tokens,
            'concurrent_structures': concurrent_structures
        }

    def __unicode__(self):
        return self.title

    class Meta:
        unique_together = (
            ('type', 'language', 'publisher', 'osis_slug', 'publish_date'),
        )


class Token(models.Model):
    """
    An atomic unit of text, such as a word, punctuation mark, or whitespace
    line break. Corresponds to OSIS w elements.
    
    What to do about tokens that don't appear in a verse? i.e. when an osisID isn't
    fully specified or doesn't exist at all? For example, introductory material
    or titles? We could just use the best available osisID, e.g. it could be as
    basic as just bookName or bookName.chapterNumber.
    
    If a hash is a duplicate with a previous hash, should the subsequent word merely
    increase the look-behind for the n-gram? This way, the subsequent change won't
    ripple. But if we change a word in the middle of a verse, and that ID conflicts
    with a subsequent one, do we really want to change the subsequent ID alone?
    It wasn't even the token that changed in the first place.
    """
    
    id = models.CharField(_("base32 sha-256 hash of [workID, passage, n-gram token context]"), max_length=52, primary_key=True)
    data = models.CharField(_("Unicode data in Normalization Form C (NFC)"), max_length=255, db_index=True)

    WORD = 1
    PUNCTUATION = 2
    WHITESPACE = 3
    TYPE_NAMES = {
        WORD: 'word',
        PUNCTUATION: 'punctuation',
        WHITESPACE: 'whitespace'
    }
    TYPE_CHOICES = (
        (WORD, TYPE_NAMES[WORD]),
        (PUNCTUATION, TYPE_NAMES[PUNCTUATION]),
        (WHITESPACE, TYPE_NAMES[WHITESPACE]),
    )
    type = models.PositiveSmallIntegerField(_("A general hint as to what the token data represents"), choices=TYPE_CHOICES, default=WORD, db_index=True)
    type_name = property(lambda self: self.TYPE_NAMES[self.type])

    position = models.PositiveIntegerField(db_index=True)
    work = models.ForeignKey(Work)
    #variant_bits = models.PositiveSmallIntegerField(_("Bitwise anded with Work.variant_bit to determine if belongs to work."), default=0b00000001)
    #unified_token = models.ForeignKey('self', null=True, help_text="The token in the merged/unified work that represents this token.")

    is_structure_marker = None #This boolean is set when querying via Structure.get_tokens

    #TODO: Make type an array?
    def get_structures(self, types = [], including_markers = False): #types = [Structure.VERSE]
        """
        Get the structures that this token is a part of.
        """
        raise Exception(_("Not implemented yet"))

    #TODO: This is where internal linked data connects with the data out in the world through hyperlinks
    #TODO: How do you query for isblank=False? Whe not say null=True?
    relative_source_url = models.CharField(_("Relative URL for where this token came from (e.g. including XPointer); %base% refers to work.src_url"), max_length=255, blank=True)

    def get_source_url(self):
        if not self.relative_source_url:
            return None

        structures = Structure.objects.filter(
            Q(start_token__position__lte = self.position),
            Q(end_token__position__gte = self.position),
            source_url__isnull = False,
            #source_url__ne = "",
            #source_url__isblank = False,
            work = self.work
        ) #.extra(where=["%s.variant_bits & %%s != 0" % Structure._meta.db_table], params=[self.variant_bits])


        if not len(structures):
            base = self.work.source_url
        else:
            #TODO: If multiple structures have source_urls?
            base = structures[0].source_url
        #TODO: What if the base isn't desired?

        return base + self.relative_source_url
    source_url = property(get_source_url)

    class Meta:
        ordering = ['position']
        unique_together = (
            ('position', 'work'),
        )

    def __unicode__(self):
        return self.data


#class StructureType(models.Model):
#    pass


class Structure(models.Model):
    """
    Represent supra-segmental structures in the text, various markup; really
    what this needs to do is represent every non-w element in OSIS.
    """
    
    ELEMENT_CHOICES = (
        # Element list
        ('a', 'a'),
        ('abbr', 'abbr'),
        ('actor', 'actor'),
        ('caption', 'caption'),
        ('castGroup', 'castGroup'),
        ('castItem', 'castItem'),
        ('castList', 'castList'),
        ('catchWord', 'catchWord'),
        ('cell', 'cell'),
        ('chapter', 'chapter'),
        ('closer', 'closer'),
        ('contributor', 'contributor'),
        ('coverage', 'coverage'),
        ('creator', 'creator'),
        ('date', 'date'),
        ('description', 'description'),
        #'div', (no need for this since promoting div[type] to full element named `type`)
        ('divineName', 'divineName'),
        ('figure', 'figure'),
        ('foreign', 'foreign'),
        ('format', 'format'),
        ('head', 'head'),
        ('header', 'header'),
        ('hi', 'hi'),
        ('identifier', 'identifier'),
        ('index', 'index'),
        ('inscription', 'inscription'),
        ('item', 'item'),
        ('l', 'l'),
        ('label', 'label'),
        ('language', 'language'),
        ('lb', 'lb'),
        ('lg', 'lg'),
        ('list', 'list'),
        ('mentioned', 'mentioned'),
        #'milestone',      (n/a since all strucutres milestoned)
        #'milestoneEnd',   (n/a since all strucutres milestoned)
        #'milestoneStart', (n/a since all strucutres milestoned)
        ('name', 'name'),
        ('note', 'note'),
        ('osis', 'osis'),
        ('osisCorpus', 'osisCorpus'),
        ('osisText', 'osisText'),
        ('p', 'p'),
        ('publisher', 'publisher'),
        ('q', 'q'),
        ('rdg', 'rdg'),
        ('rdgGrp', 'rdgGrp'),
        ('refSystem', 'refSystem'),
        ('reference', 'reference'),
        ('relation', 'relation'),
        ('revisionDesc', 'revisionDesc'),
        ('rights', 'rights'),
        ('role', 'role'),
        ('roleDesc', 'roleDesc'),
        ('row', 'row'),
        ('salute', 'salute'),
        ('scope', 'scope'),
        ('seg', 'seg'),
        ('seq', 'seq'),
        ('signed', 'signed'),
        ('source', 'source'),
        ('speaker', 'speaker'),
        ('speech', 'speech'),
        ('subject', 'subject'),
        ('table', 'table'),
        ('teiHeader', 'teiHeader'),
        ('title', 'title'),
        ('titlePage', 'titlePage'),
        ('transChange', 'transChange'),
        ('type', 'type'),
        ('verse', 'verse'),
        ('w', 'w'),
        ('work', 'work'),

        # Promoting div[type] elements to elements of the name [type]
        ('acknowledgement', 'acknowledgement'),
        ('afterword', 'afterword'),
        ('annotant', 'annotant'),
        ('appendix', 'appendix'),
        ('article', 'article'),
        ('back', 'back'),
        ('body', 'body'),
        ('book', 'book'),
        ('bookGroup', 'bookGroup'),
        #'chapter', (use existing element above)
        ('colophon', 'colophon'),
        ('commentary', 'commentary'),
        ('concordance', 'concordance'),
        ('coverPage', 'coverPage'),
        ('dedication', 'dedication'),
        ('devotional', 'devotional'),
        ('entry', 'entry'),
        ('front', 'front'),
        ('gazetteer', 'gazetteer'),
        ('glossary', 'glossary'),
        ('imprimatur', 'imprimatur'),
        #'index', (use existing element above)
        ('introduction', 'introduction'),
        ('majorSection', 'majorSection'),
        ('map', 'map'),
        #'paragraph', (use existing element above)
        ('part', 'part'),
        ('preface', 'preface'),
        ('section', 'section'),
        ('subSection', 'subSection'),
        ('summary', 'summary'),
        #'titlePage', (use existing element above)
        
        # New elements
        ('page', 'page'), # used to preserve page boundaries; TEI?
        
        # Proposed
        #('doubted', 'doubted'), #level1 and level2? rdg?
    )
    
    element = models.CharField(max_length=32, blank=False, help_text=_("The name of the OSIS "), choices=ELEMENT_CHOICES)
    # Note: attributes is a related_name for StructureAttribute
    # Question: what about using XMLField? Or storing attributes via GeoDjango.DictionaryField

    osis_id = models.CharField(max_length=32, blank=True, db_index=True) # the one attribute moved to StructureAttribute
    work = models.ForeignKey(Work, help_text=_("Must be same as start/end_*_token.work. Must not be a variant work; use the variant_bits to select for it"))
    #variant_bits = models.PositiveSmallIntegerField(default=0b00000001, help_text=_("Bitwise anded with Work.variant_bit to determine if belongs to work."))

    source_url = models.CharField(max_length=255, blank=True, help_text=_("URL for where this structure came from; used for base to Token.relative_source_url"))
    
    position = models.PositiveIntegerField(help_text=_("The order where this appears in the work. Note that this does not need to be unique since two structures could start at the same position."))

    numerical_start = models.PositiveIntegerField(null=True, help_text=_("A number that may be associated with this structure, such as a chapter or verse number; corresponds to OSIS @n attribute."))
    numerical_end   = models.PositiveIntegerField(null=True, help_text=_("If the structure spans multiple numerical designations, this is used"))

    start_token = models.ForeignKey(Token, null=True, related_name='start_token_structure_set', help_text=_("The token that starts the structure's content; this may or may not include the start_marker, like quotation marks. <del>If null, then tokens should be discovered via StructureToken.</del>"))
    end_token   = models.ForeignKey(Token, null=True,  related_name='end_token_structure_set',  help_text=_("Same as start_token, but for the end."))

    # Used to demarcate the inclusive start point for the structure; marks any typographical feature used to markup the structure in the text (e.g. quotation marks).
    start_marker = models.ForeignKey(Token, null=True, related_name='start_marker_structure_set', help_text=_("The optional token that marks the start of the structure; this marker may be included (inside) in the start_token/end_token range as in the example of quotation marks, or it may excluded (outside) as in the case of paragraph markers which are double linebreaks. Outside markers may overlap (be shared) among multiple paragraphs' start/end_markers, whereas inside markers may not."))
    end_marker   = models.ForeignKey(Token, null=True, related_name='end_marker_structure_set',   help_text=_("Same as start_marker, but for the end."))

    @property
    def tokens(self, include_outside_markers = False, variant_bits = None):
        if include_outside_markers:
            raise Exception(_("include_outside_markers not implemented yet"))
        #if variant_bits is None:
        #    variant_bits = self.variant_bits
        
        assert(self.end_marker is not None)
        
        # Get all of the tokens between the marker start and marker end
        # and who have variant bits that match the requested variant bits
        tokens = Token.objects.filter(
            work = self.work,
            position__gte = self.start_token.position,
            position__lte = self.end_token.position
        ) #.extra(where=['variant_bits & %s != 0'], params=[variant_bits])
        
        return tokens

    # Get rid of the bitwise stuff here? Just use the string identifiers?
    SHADOW_NONE  = 0b0000
    SHADOW_START = 0b0001
    SHADOW_END   = 0b0010
    SHADOW_BOTH  = 0b0011
    SHADOW_NAMES = {
        SHADOW_NONE:'none',
        SHADOW_START:'start',
        SHADOW_END:'end',
        SHADOW_BOTH:'both'
    }
    SHADOW_CHOICES = (
        (SHADOW_NONE,  SHADOW_NAMES[SHADOW_NONE]),
        (SHADOW_START, SHADOW_NAMES[SHADOW_START]),
        (SHADOW_END,   SHADOW_NAMES[SHADOW_END]),
        (SHADOW_BOTH,  SHADOW_NAMES[SHADOW_BOTH])
    )
    shadow = SHADOW_NONE
    shadow_name = property(lambda self: self.SHADOW_NAMES[self.shadow])

    #@property
    #def related_structures(self, elements = [], shadow = SHADOW_NONE):
    #    """
    #    Get the structures that are related to this structure.
    #    
    #    types is a list of TYPE that should be returned. Empty means all.
    #    
    #    If shadow = SHADOW_NONE, then only sub-structures are returned;
    #    If shadow = SHADOW_BOTH, then only super-structures are returned.
    #    If shadow = SHADOW_START, then only structures that start before
    #    If shadow = SHADOW_END, then only structures that end after
    #    """
    #    raise Exception(_("Not built yet"))


    class Meta:
        ordering = ['position'] #, 'variant_number'
        unique_together = (
            ('element', 'position', 'start_token'), #???
        )

    def __unicode__(self):
        if self.osis_id:
            return self.osis_id
        elif self.element == 'p': #paragraph
            return u"¶" + self.start_token.data + u" … " + self.end_token.data
        elif self.element == self.UNCERTAIN1:
            return u"[]"
        else:
            return self.type


class StructureAttribute(models.Model):
    """
    Basically an OSIS XML attribute for an associated structure which is an OSIS XML element.
    
    The attributes allowed for a Structure should be constrained based on the schema.
    """
    structure = models.ForeignKey(Structure, blank=False, related_name='attributes', help_text=_("The structure that the attributes are for"))
    name = models.CharField(max_length=32, blank=False, help_text=_("The name of the attribute. May include a limited number of discrete XML namespace prefixes, e.g. 'xml:'."), db_index=True)
    value = models.TextField(db_index=True, help_text=_("The attribute value."))
    
    # TODO: Value validation
    #TYPE_CHOICES = (
    #    ('string', "String"),
    #    ('boolean', "Boolean"),
    #    ('datetime', "Date/Time"),
    #    ('langiage', "Language"),
    #    ('osisRef', "osisRef"),
    #    ('osisID', "osisID"),
    #    ('ID', "ID"), #does this even make sense?
    #)
    #_ATTRIBUTE_TYPES = {
    #    'osisID': 'osisID',
    #}
    #type = models.CharField(max_length=32, blank=False, choices=TYPE_CHOICES)
    
    class Meta:
        unique_together = (
            ('structure', 'name'), # only allow one 
        )
    

# This is an alternative to the above and it allows non-consecutive tokens to be
# included in a structure. But it incurs a huge amount of overhead. If
# start_token is null, then it could be assumed that a structure's tokens should
# be found via StructureToken
#class StructureToken(models.Model):
#    """
#    Non-consecutive tokens can be assigned to a Structure via this model.
#    """
#    structure = models.ForeignKey(Structure)
#    token = models.ForeignKey(Token)
#    is_marker = models.BooleanField(default=False, help_text=_("Whether the token is any such typographical feature which marks up the structure in the text, such as a quotation mark."))


################################################################################
# Linked Token Data
################################################################################


# These relate to interlinearization; these could also be used for unification
# instead of relying on Token.unified_token
# TODO: This can also be used to associate words with a note; otherwise, start_token/end_token would be used
class TokenLinkage(models.Model):
    """
    Anchor point to link together multiple TokenLinkageItems
    """
    #TODO: We need to have a type field, e.g. translation
    #      And it would be good to have a strength field from 0.0 to 1.0
    UNIFICATION = 1
    TRANSLATION = 2
    CROSS_REFERENCE = 3
    TYPE_CHOICES = (
        (UNIFICATION, _("Link the result of unification/merging algorithm")),
        (TRANSLATION, _("Incoming token is translation of outgoing token")),
        (CROSS_REFERENCE, _("Related passage")),
    )
    type = models.PositiveIntegerField(null=True, choices=TYPE_CHOICES, help_text=_("The kind of linkage"))
    key = models.CharField(db_index=True, max_length=100, help_text=_("Key (hash) of each item's token's unambiguous work osisID and position sorted, utilizing ranges whenever possible. Must be updated whenever an item is added or removed. Examples: ESV.2001:4-8;KJV.1611:3-6;NIV:2,4,6-9. Note how contiguous tokens are indicated with a hyphen range, how non-contiguous tokens are separated by commas, and how tokens from different works are separated by semicolons. All are sorted; the token items of a TokenLinkage do not have position. There is only one key for one collection of tokens."))
    #TODO: The type is not factored in here.


class TokenLinkageItem(models.Model):
    """
    Tokens from different works can be linked together by instantiating
    TokenLinkageItems and associating them with the same TokenLinkage.
    If the token being linked is not local, then the `token_work` and
    `token_position` must be defined and `token` must be null. Otherwise, if
    `token` is not null then `token_work`
    """
    linkage = models.ForeignKey(TokenLinkage)

    #Note: token.Meta.unique_together == ('position', 'work') so it can be used
    #      as a composite key. This can be employed instead of token =
    #      models.ForeignKey(Token) so that the actual token referenced may
    #      exist on another system whose internal ID is unknown.
    #      Constraint for Django 1.2:
    #        token.position == token_position &&
    #        token.work     == token_work
    token_position = models.PositiveIntegerField(db_index=True)
    token_work = models.ForeignKey(Work)
    #token = models.ForeignKey(Token, null=True)
    #UPDATE: Remove `token` completely? Otherwise, if not removed
    #        we could have an ON UPDATE trigger for token that updates
    #        all TokenLinkageItems that point to it

    weight = models.DecimalField(null=True, help_text=_("The strength of the linkage; value between 0.0 and 1.0."), max_digits=3, decimal_places=2)
    INCOMING = 0b01
    OUTGOING = 0b10
    BIDIRECTIONAL = 0b11
    DIRECTIONALITY_CHOICES = (
        (INCOMING, _("Incoming unidirectional link")),
        (OUTGOING, _("Outgoing unidirectional link")),
        (BIDIRECTIONAL, _("Bidirectional link")),
    )
    directionality = models.PositiveIntegerField(default=BIDIRECTIONAL, choices=DIRECTIONALITY_CHOICES, help_text=_("Whether the link"))


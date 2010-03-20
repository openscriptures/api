# coding: utf8 #

from django.db import models
from django.db.models import Q
#from api.osis import *






class Language(models.Model):
    "A human language, either ancient or modern."
    
    code = models.CharField("ISO 639-3 language code", max_length=10, primary_key=True)
    name = models.CharField(max_length=32)
    DIRECTIONS = (
        ('ltr', 'Left to Right'),
        ('rtl', 'Right to Left'),
        #also needing vertical directions, see CSS writing-mode
    )
    direction = models.CharField("Text directionality", max_length=3, choices=DIRECTIONS, default='ltr')
    
    def __unicode__(self):
        return self.name



class License(models.Model):
    "A license that a work uses to indicate the copyright restrictions or permissions."
    
    name = models.CharField(max_length=128)
    abbreviation = models.CharField(max_length=32, blank=True, db_index=True)
    url = models.URLField(blank=True, help_text="Primary URL which defines the license.")
    
    # We need a matrix describing what the license allows:
    # - attribution
    # - noncommercial
    # - share_alike
    # - nonderivative
    isolatable = models.BooleanField(default=True, help_text="If this is true, then this work can be displayed independently. Otherwise, it must only be displayed in conjunction with other works. Important condition for fair use license.")
    
    def __unicode__(self):
        return self.name


class Server(models.Model):
    """
    A server that hosts the Open Scriptures API
    """
    is_self = models.BooleanField(help_text="Whether the server refers to itself")
    base_url = models.URLField(help_text="The base URL that the API URIs can be appended to.")
    version = models.CharField(max_length=5, default="1")
    #Idea: adapters for URL rewriting and response transformation so that servers need not be compatible with Open Scriptures API


class WorkServer(models.Model):
    """
    Intermediary table for ManyToMany relationship between Work and Server
    """
    is_primary = models.BooleanField(help_text="Whether the server is canonical (primary) or not (mirror)")
    work = models.ForeignKey('Work')
    server = models.ForeignKey('Server')


class Work(models.Model):
    "Represents an OSIS work, such as the Bible or a non-biblical work such as the Qur'an or the Mishnah."
    
    title = models.CharField(max_length=255)
    abbreviation = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    source_url = models.URLField(blank=True, help_text="URL where this resource was originally obtained")
    
    variants_for_work = models.ForeignKey('self', null=True, default=None, verbose_name="Parent work that this work provides variants for")
    variant_bit = models.PositiveSmallIntegerField(default=0b00000001, help_text="The bit mask that is anded with Token.variant_bits and TokenStructure.variant_bits to query only those which belong to the work.")
    
    #TODO: Important to allow mutliple kinds of identifiers for the work!
    #      Including ISBN, URL, URN, in addition to OSIS. OSIS needs to be unique,
    #      and its parts should be deconstructable.
    
    #Bible.en.Publisher.ABC.2010
    #TODO: this should be pulled from osis.TYPES
    TYPES = (
        ('Bible', 'Bible'),
    )
    #TODO: use short_name?
    osis_slug = models.SlugField(max_length=16, db_index=True, help_text="OSIS identifier which should correspond to the abbreviation, like NIV, ESV, or KJV")
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
    publish_date = models.DateField(null=True, db_index=True, help_text="When the work was published")
    import_date = models.DateField(null=True, help_text="When the work was imported into the models.")
    
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
    
    #unified_work = models.ForeignKey('self', null=True, verbose_name="Work which this work has been merged into")
    
    
    def lookup_osis_ref(self, start_osis_id, end_osis_id = None, variant_bits = None):
        if not end_osis_id:
            end_osis_id = start_osis_id
        
        # Token and TokenStructure objects are only associated with non-diff
        #   works, that is where variants_for_work is None
        main_work = self
        if self.variants_for_work is not None:
            main_work = self.variants_for_work
        
        # Allow the variant_bits to be customized to include structures and
        #   tokens from other variants of this work
        if variant_bits is None:
            variant_bits = self.variant_bit
        
        # Get the structure for the start
        structures = TokenStructure.objects.select_related(depth=1).filter(
            work = main_work,
            start_token__isnull = False,
            osis_id = start_osis_id
        ).extra(where=["variant_bits & %s != 0"], params=[variant_bits])
        if len(structures) == 0:
            raise Exception("Start structure with osisID %s not found" % start_osis_id)
        start_structure = structures[0]
        
        # Get the structure for the end
        if start_osis_id != end_osis_id:
            structures = TokenStructure.objects.select_related(depth=1).filter(
                work = main_work,
                end_token__isnull = False,
                osis_id = end_osis_id
            ).extra(where=["variant_bits & %s != 0"], params=[variant_bits])
            if len(structures) == 0:
                raise Exception("End structure with osisID %s not found" % end_osis_id)
            end_structure = structures[0]
        else:
            end_structure = start_structure
        
        # Now grab all structures from the work which have start/end_token or
        #  start/end_marker whose positions are less 
        concurrent_structures = TokenStructure.objects.select_related(depth=1).filter(work = main_work).filter(
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
        ).extra(where=["api_tokenstructure.variant_bits & %s != 0"], params=[variant_bits])
        
        # Now indicate if the structures are shadowed (virtual)
        for struct in concurrent_structures:
            if struct.start_token.position < start_structure.start_token.position:
                struct.shadow = struct.shadow | TokenStructure.SHADOW_START
            if struct.end_token.position > end_structure.end_token.position:
                struct.shadow = struct.shadow | TokenStructure.SHADOW_END
        
        # Now get all tokens that exist between the beginning of start_structure
        # and the end of end_structure
        
        # Get all of the tokens between the start and end and who have variant
        # bits that match the requested variant bits
        tokens = Token.objects.filter(
            work = main_work,
            position__gte = start_structure.start_token.position,
            position__lte = end_structure.end_token.position
        ).extra(where=['variant_bits & %s != 0'], params=[variant_bits])
        
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
    "An atomic unit of text, such as a word, punctuation mark, or whitespace line break. Corresponds to OSIS w elements."
    data = models.CharField(max_length=255, db_index=True, help_text="Unicode data in Normalization Form C (NFC)")
    
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
    type = models.PositiveSmallIntegerField(choices=TYPE_CHOICES, default=WORD, db_index=True, help_text="A general hint as to what the token data represents")
    type_name = property(lambda self: self.TYPE_NAMES[self.type])
    
    position = models.PositiveIntegerField(db_index=True)
    work = models.ForeignKey(Work)
    variant_bits = models.PositiveSmallIntegerField(default=0b00000001, help_text="Bitwise anded with Work.variant_bit to determine if belongs to work.")
    #unified_token = models.ForeignKey('self', null=True, help_text="The token in the merged/unified work that represents this token.")
    
    is_structure_marker = None #This boolean is set when querying via TokenStructure.get_tokens
    
    #TODO: Make type an array?
    def get_structures(self, types = [], including_markers = False): #types = [TokenStructure.VERSE]
        "Get the structures that this token is a part of."
        raise Exception("Not implemented yet")
    
    
    #TODO: This is where internal linked data connects with the data out in the world through hyperlinks
    #TODO: How do you query for isblank=False? Whe not say null=True?
    relative_source_url = models.CharField(max_length=255, blank=True, help_text="Relative URL for where this token came from (e.g. including XPointer); %base% refers to work.src_url")
    
    def get_source_url(self):
        if not self.relative_source_url:
            return None
        
        structures = TokenStructure.objects.filter(
            Q(start_token__position__lte = self.position),
            Q(end_token__position__gte = self.position),
            source_url__isnull = False,
            #source_url__ne = "",
            #source_url__isblank = False,
            work = self.work
        ).extra(where=["api_tokenstructure.variant_bits & %s != 0"], params=[self.variant_bits])
        
        
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



class TokenStructure(models.Model):
    "Represent supra-segmental structures in the text, various markup; really what this needs to do is represent every non-w element in OSIS."
    
    #Todo: Is there a better way of doing these enumerations? Integers chosen
    #      instead of a CharField to save space.
    #TODO: We need to be able to represent a lot more than this! To faithfully
    #      store OSIS, it will need be able to represent every feature.
    #      The various structure types each need to have a certain number of
    #      possible attribues? Idea: why not just store the OSIS element name in
    #      one field, and then store all of the the attributes in another? When
    #      serializing out the data as-is into XML, it would result in
    #      overlapping hierarchies, so then whichever structure is desired could
    #      then be presented.
    
    
    BOOK_GROUP = 1
    BOOK = 2
    CHAPTER = 3
    VERSE = 4
    SECTION = 5
    SUBSECTION = 6
    TITLE = 7
    PARAGRAPH = 8
    LINE = 9
    QUOTATION = 10
    UNCERTAIN1 = 11
    UNCERTAIN2 = 12
    PAGE = 13
    TYPE_NAMES = {
        BOOK_GROUP: "bookGroup",
        BOOK: "book",
        CHAPTER: "chapter",
        VERSE: "verse",
        SECTION: "section",
        SUBSECTION: "subSection",
        TITLE: "title",
        PARAGRAPH: "paragraph",
        LINE: "line",
        QUOTATION: "quotation",
        UNCERTAIN1: "uncertain-1", #single square brackets around tokens
        UNCERTAIN2: "uncertain-2", #double square brackets around tokens
        PAGE: "page",
        #TODO: KJV “supplied” phrase
    }
    TYPE_CHOICES = (
        (BOOK_GROUP, TYPE_NAMES[BOOK_GROUP]),
        (BOOK, TYPE_NAMES[BOOK]),
        (CHAPTER, TYPE_NAMES[CHAPTER]),
        (VERSE, TYPE_NAMES[VERSE]),
        (SECTION, TYPE_NAMES[SECTION]),
        (SUBSECTION, TYPE_NAMES[SUBSECTION]),
        (TITLE, TYPE_NAMES[TITLE]),
        (PARAGRAPH, TYPE_NAMES[PARAGRAPH]),
        (LINE, TYPE_NAMES[LINE]),
        (QUOTATION, TYPE_NAMES[QUOTATION]),
        (UNCERTAIN1, TYPE_NAMES[UNCERTAIN1]), #single square brackets around tokens
        (UNCERTAIN2, TYPE_NAMES[UNCERTAIN2]), #double square brackets around tokens
        (PAGE, TYPE_NAMES[PAGE]),
        #...
    )
    type = models.PositiveSmallIntegerField(choices=TYPE_CHOICES, db_index=True)
    type_name = property(lambda self: self.TYPE_NAMES[self.type])
    
    osis_id = models.CharField(max_length=32, blank=True, db_index=True)
    work = models.ForeignKey(Work, help_text="Must be same as start/end_*_token.work. Must not be a variant work; use the variant_bits to select for it")
    variant_bits = models.PositiveSmallIntegerField(default=0b00000001, help_text="Bitwise anded with Work.variant_bit to determine if belongs to work.")
    
    source_url = models.CharField(max_length=255, blank=True, help_text="URL for where this structure came from; used for base to Token.relative_source_url")
    
    # title?
    # parent?
    position = models.PositiveIntegerField(help_text="The order where this appears in the work.")
    
    numerical_start = models.PositiveIntegerField(null=True, help_text="A number that may be associated with this structure, such as a chapter or verse number; corresponds to OSIS @n attribute.")
    numerical_end   = models.PositiveIntegerField(null=True, help_text="If the structure spans multiple numerical designations, this is used")
    
    start_token = models.ForeignKey(Token, null=True, related_name='start_token_structure_set', help_text="The token that starts the structure's content; this may or may not include the start_marker, like quotation marks. If null, then tokens should be discovered via TokenStructureItem.")
    end_token   = models.ForeignKey(Token, null=True, related_name='end_token_structure_set',   help_text="Same as start_token, but for the end.")
    
    #Used to demarcate the inclusive start point for the structure; marks any typographical feature used to markup the structure in the text (e.g. quotation marks).
    start_marker = models.ForeignKey(Token, null=True, related_name='start_marker_structure_set', help_text="The optional token that marks the start of the structure; this marker may be included (inside) in the start_token/end_token range as in the example of quotation marks, or it may excluded (outside) as in the case of paragraph markers which are double linebreaks. Outside markers may overlap (be shared) among multiple paragraphs' start/end_markers, whereas inside markers may not.")
    end_marker   = models.ForeignKey(Token, null=True, related_name='end_marker_structure_set',   help_text="Same as start_marker, but for the end.")
    
    def get_tokens(self, include_outside_markers = False, variant_bits = None):
        if include_outside_markers:
            raise Exception("include_outside_markers not implemented yet")
        if variant_bits is None:
            variant_bits = self.variant_bits
        
        # Get the tokens from a range
        if self.start_token is not None:
            assert(self.end_marker is not None)
            
            # Get all of the tokens between the marker start and marker end
            # and who have variant bits that match the requested variant bits
            tokens = Token.objects.filter(
                work = self.work,
                position__gte = self.start_token.position,
                position__lte = self.end_token.position
            ).extra(where=['variant_bits & %s != 0'], params=[variant_bits])
            
            # Indicate which of the beginning queried tokens are markers
            #for token in tokens:
            #    if token.position >= start_structure.start_token.position:
            #        break
            #    token.is_structure_marker = True
            #
            ## Indicate which of the ending queried tokens are markers
            #for token in reversed(tokens):
            #    if token.position <= end_structure.end_token.position:
            #        break
            #    token.is_structure_marker = True
            
            return tokens
        
        # Get the tokens which are not consecutive
        else:
            items = TokenStructureItem.objects.extra(where=["token__variant_bits & %s != 0"], params=[variant_bits])
            tokens = []
            for item in items:
                items.token.is_structure_marker = item.is_marker
                tokens.append(items.token)
            return tokens
    
    tokens = property(get_tokens)
    
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
    
    is_milestoned = False
    
    #TODO: Include a type filter?
    def get_related_structures(self, types = [], shadow = SHADOW_NONE):
        """
        Get the structures that are related to this structure.
        types is a list of TYPE that should be returned. Empty means all.
        If shadow = SHADOW_NONE, then only sub-structures are returned;
        If shadow = SHADOW_BOTH, then only super-structures are returned.
        If shadow = SHADOW_START, then only structures that start before
        If shadow = SHADOW_END, then only structures that end after
        """
        raise Exception("Not built yet")
    
    
    class Meta:
        ordering = ['position'] #, 'variant_number'
        unique_together = (
            ('type', 'position', 'start_token'), #???
        )
    
    def __unicode__(self):
        if self.osis_id:
            return self.osis_id
        elif self.type == self.PARAGRAPH:
            return u"¶" + self.start_token.data + u" … " + self.end_token.data
        elif self.type == self.UNCERTAIN1:
            return u"[]"
        else:
            return self.type



# This is an alternative to the above and it allows non-consecutive tokens to be
# included in a structure. But it incurs a huge amount of overhead. If
# start_token is null, then it could be assumed that a structure's tokens should
# be found via TokenStructureItem
class TokenStructureItem(models.Model):
    "Non-consecutive tokens can be assigned to a TokenStructure via this model."
    structure = models.ForeignKey(TokenStructure)
    token = models.ForeignKey(Token)
    is_marker = models.BooleanField(default=False, help_text="Whether the token is any such typographical feature which marks up the structure in the text, such as a quotation mark.")


################################################################################
# Linked Token Data
################################################################################


# These relate to interlinearization; these could also be used for unification
# instead of relying on Token.unified_token
# TODO: This can also be used to associate words with a note; otherwise, start_token/end_token would be used
class TokenLinkage(models.Model):
    "Anchor point to link together multiple TokenLinkageItems"
    #TODO: We need to have a type field, e.g. translation
    #      And it would be good to have a strength field from 0.0 to 1.0
    UNIFICATION = 1
    TRANSLATION = 2
    CROSS_REFERENCE = 3
    TYPE_CHOICES = (
        (UNIFICATION, "Link the result of unification/merging algorithm"),
        (TRANSLATION, "Incoming token is translation of outgoing token"),
        (CROSS_REFERENCE, "Related passage"),
    )
    type = models.PositiveIntegerField(null=True, choices=TYPE_CHOICES, help_text="The kind of linkage")
    key = models.CharField(db_index=True, max_length=100, help_text="Key (hash) of each item's token's unambiguous work osisID and position sorted, utilizing ranges whenever possible. Must be updated whenever an item is added or removed. Examples: ESV.2001:4-8;KJV.1611:3-6;NIV:2,4,6-9. Note how contiguous tokens are indicated with a hyphen range, how non-contiguous tokens are separated by commas, and how tokens from different works are separated by semicolons. All are sorted; the token items of a TokenLinkage do not have position. There is only one key for one collection of tokens.")
    #TODO: The type is not factored in here.


class TokenLinkageItem(models.Model):
    """
    Tokens from different works can be linked together by instantiating
    TokenLinkageItems and associating them with the same TokenLinkage.
    If the token being linked is not local, then the `token_work` and `token_position`
    must be defined and `token` must be null. Otherwise, if `token` is not null
    then `token_work`
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
    
    weight = models.DecimalField(null=True, help_text="The strength of the linkage; value between 0.0 and 1.0.", max_digits=3, decimal_places=2)
    INCOMING = 0b01
    OUTGOING = 0b10
    BIDIRECTIONAL = 0b11
    DIRECTIONALITY_CHOICES = (
        (INCOMING, "Incoming unidirectional link"),
        (OUTGOING, "Outgoing unidirectional link"),
        (BIDIRECTIONAL, "Bidirectional link"),
    )
    directionality = models.PositiveIntegerField(default=BIDIRECTIONAL, choices=DIRECTIONALITY_CHOICES, help_text="Whether the link")




################################################################################
# Token Metadata
################################################################################

class TokenMeta(models.Model):
    "Metadata about each token, including language, parsing information, etc."

    token = models.ForeignKey(Token, related_name="token_parsing_set")
    work = models.ForeignKey(Work, null=True, blank=True, help_text="The work that defines this parsing; may be null since a user may provide it. Usually same as token.work")
    language = models.ForeignKey(Language, null=True, blank=True, help_text="The language of the token. Not necessarily the same as token.work.language")
    # TODO: Should be changed to a ForeignKey linking to strongs db when that comes online
    strongs = models.CharField(max_length=255, help_text="The strongs number, prefixed by 'H' or 'G' specifying whether it is for the Hebrew or Greek, respectively. Multiple numbers separated by semicolon.")
    # TODO: Lemma should probably expressed in TokenParsing_* objects,
    #       since there can be a difference of opinion in some cases.
    lemma = models.CharField(max_length=255, help_text="The lemma chosen for this token. Need not be supplied if strongs given. If multiple lemmas are provided, then separate with semicolon.")

    # TODO: Get these TokenParsing models established
    def get_parsing(self):
        if self.language.code == "grc":
            return TokenParsing_grc.objects.get(tokenmeta = self)
        elif self.language.code == "hbo":
            return TokenParsing_hbo.objects.get(tokenmata = self)
        else:
            raise Error("Unknown parsing language.")

    parsing = property(get_parsing)



class TokenParsing_grc(models.Model):
    "Represent Greek parsing information for a given Token."

    tokenmeta = models.ForeignKey(TokenMeta)
    # Choicse here
    # From Smyth's grammar
    PARTS_OF_SPEECH = (
        ('Noun','Noun'),
        ('Adjective','Adjective'),
        ('Pronoun','Pronoun'),
        ('Verb','Verb'),
        ('Adverb','Adverb'),
        ('Preposition','Preposition'),
        ('Conjunction','Conjunction'),
        ('Particle','Particle'),
    )

    NUMBERS = (
        ('Singular','Singular'),
        ('Dual','Dual'),
        ('Plural','Plural'),
    )

    GENDERS = (
        ('Masculine','Masculine'),
        ('Feminine','Feminine'),
        ('Neuter','Neuter'),
    )

    CASES = (
        ('Nominative','Nominative'),
        ('Genitive','Genitive'),
        ('Dative','Dative'),
        ('Accusative','Accusative'),
        ('Vocative','Vocative'),
    )

    # TODO: Should 2nd aorist be expressed here, or have its own field?
    TENSES = (
        ('Present','Present'),
        ('Imperfect','Imperfect'),
        ('Future','Future'),
        ('Aorist','Aorist'),
        ('Perfect','Perfect'),
        ('Pluperfect','Pluperfect'),
        ('Future Perfect','Future Perfect'),
    )

    VOICES = (
        ('Active','Active'),
        ('Middle','Middle'),
        ('Passive','Passive'),
    )

    MOODS = (
        ('Indicative','Indicative'),
        ('Subjunctive','Subjunctive'),
        ('Optative','Optative'),
        ('Imperative','Imperative'),
        ('Infinitive','Infinitive'),
        ('Participle','Participle'),
    )

    PERSONS = (
        ('First','First'),
        ('Second','Second'),
        ('Third','Third'),
    )

    # Fields here
    part = models.CharField(max_length=12, choices=PARTS_OF_SPEECH)
    substantival_number = models.CharField(max_length=12, choices=NUMBERS, blank=True)
    gender = models.CharField(max_length=12, choices=GENDERS, blank=True)
    case = models.CharField(max_length=12, choices=CASES, blank=True)
    tense = models.CharField(max_length=20, choices=TENSES, blank=True)
    voice = models.CharField(max_length=12, choices=VOICES, blank=True)
    mood = models.CharField(max_length=20, choices=MOODS, blank=True)
    person = models.CharField(max_length=12, choices=PERSONS, blank=True)
    verbal_number = models.CharField(max_length=12, choices=NUMBERS, blank=True)

    # TODO: Model validation for parsings based on part of speech, mood, etc.



class TokenParsing_hbo(models.Model):
    "Represent Hebrew parsing information for a given Token."

    tokenmeta = models.ForeignKey(TokenMeta)
    # TODO: Create the rest of the parsing model




    


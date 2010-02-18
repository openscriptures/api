# coding: utf8 #

from django.db import models
from django.db.models import Q



class Language(models.Model):
    "A human language, either ancient or modern."
    
    code = models.CharField("ISO language code", max_length=10, primary_key=True)
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
    abbreviation = models.CharField(max_length=32, null=True, db_index=True)
    url = models.URLField(null=True, help_text="Primary URL which defines the license.")
    
    # We need a matrix describing what the license allows:
    # - attribution
    # - noncommercial
    # - share_alike
    # - nonderivative
    isolatable = models.BooleanField(default=True, help_text="If this is true, then this work can be displayed independently. Otherwise, it must only be displayed in conjunction with other works. Important condition for fair use license.")
    
    def __unicode__(self):
        return self.name


class Work(models.Model):
    "Represents an OSIS work, such as the Bible or a non-biblical work such as the Qur'an or the Mishnah."
    
    title = models.CharField(max_length=255)
    abbreviation = models.CharField(max_length=255, null=True)
    description = models.TextField(null=True)
    src_url = models.URLField(null=True, help_text="URL where this resource was originally obtained")
    
    variants_for_work = models.ForeignKey('self', null=True, default=None, verbose_name="Parent work that this work provides variants for")
    variant_bit = models.PositiveSmallIntegerField(default=0b00000001, help_text="The bit mask that is anded with Token.variant_bits and TokenStructure.variant_bits to query only those which belong to the work.")
    
    #Bible.en.Publisher.ABC.2010
    TYPES = (
        ('Bible', 'Bible'),
    )
    type = models.CharField(max_length=16, choices=TYPES, null=False)
    language = models.ForeignKey(Language, null=True)
    #Note: In the case of Daniel, both Hebrew and Aramaic in the book, though
    #      Hebrew is predominat; in this case, Work.language would still be 'hbo'; the
    #      language of the individual Tokens in the work can be indicated in a
    #      separate TokenMetadata model. This would allow multiple languages to be
    #      associated with a Token as there may be different opinions about what
    #      language it is!
    
    publisher = models.CharField(null=True, max_length=128)
    osis_slug = models.SlugField(max_length=16, help_text="OSIS identifier which should correspond to the abbreviation, like NIV, ESV, or KJV")
    publish_date = models.DateField(null=True, help_text="When the work was published")
    #Concatenation of previous fields:
    osis_id = models.CharField(max_length=32, choices=TYPES, null=False, db_index=True)
    
    copyright = models.TextField(null=True)
    license = models.ForeignKey(License)
    
    import_date = models.DateField(null=True, help_text="When the work was imported into the models.")
    
    #unified_work = models.ForeignKey('self', null=True, verbose_name="Work which this work has been merged into")
    
    
    
    def get_tokens_by_osis_ref(self, start_osis_id, end_osis_id = None, variant_bits = None):
        mainWork = self
        if self.variants_for_work:
            mainWork = self.variants_for_work
        if variant_bits is None:
            variant_bits = self.variant_bit
        
        start_structure = TokenStructure.objects.get(osis_id = start_osis_id)
        end_structure   = TokenStructure.objects.get(osis_id = end_osis_id)
        
        return Token.objects.filter(
            work = mainWork
        ).extra(where=['variant_bits & %s != 0'], params=[variant_bits]);

    
    def __unicode__(self):
        return self.title



class Token(models.Model):
    "An atomic unit of text, such as a word, punctuation mark, or whitespace line break. Corresponds to OSIS w elements."
    data = models.CharField(max_length=255, db_index=True, help_text="Unicode data in Normalization Form C (NFC)")
    
    WORD = 1
    PUNCTUATION = 2
    WHITESPACE = 3
    TYPES = (
        (WORD,        'Word'),
        (PUNCTUATION, 'Punctuation'),
        (WHITESPACE,  'Whitespace'),
    )
    type = models.PositiveSmallIntegerField(choices=TYPES, default=WORD, db_index=True)
    position = models.PositiveIntegerField(db_index=True)
    work = models.ForeignKey(Work)
    variant_bits = models.PositiveSmallIntegerField(default=0b00000001, help_text="Bitwise anded with Work.variant_bit to determine if belongs to work.")
    unified_token = models.ForeignKey('self', null=True, help_text="The token in the merged/unified work that represents this token.")
    
    #TODO: This is where internal linked data connects with the data out in the world through hyperlinks
    src_href = models.CharField(max_length=255, null=True, help_text="XPointer to where this token came from; base URL is work.src_url")
    
    #Note: Token metadata (e.g. parsings) would be stored in a separate location, e.g. TokenMeta model
    
    class Meta:
        ordering = ['position'] #, 'variant_number'
        #Note: This unique constraint is removed due to the fact that in MySQL, the default utf8 collation means "Και" and "καὶ" are equivalent
        #unique_together = (
        #    ('data', 'position', 'work'),
        #)
    
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
    QUOTATION = 9
    UNCERTAIN1 = 10
    UNCERTAIN2 = 11
    PAGE = 12
    TYPES = (
        (BOOK_GROUP, "bookGroup"),
        (BOOK, "book"),
        (CHAPTER, "chapter"),
        (VERSE, "verse"),
        (SECTION, "section"),
        (SUBSECTION, "subSection"),
        (TITLE, "title"),
        (PARAGRAPH, "paragraph"),
        (QUOTATION, "quotation"),
        (UNCERTAIN1, "uncertain-1"), #single square brackets around tokens
        (UNCERTAIN2, "uncertain-2"), #double square brackets around tokens
        (PAGE, "page"),
    )
    type = models.PositiveSmallIntegerField(choices=TYPES, db_index=True)
    osis_id = models.CharField(max_length=32, null=True, db_index=True)
    
    #position?
    numerical_start = models.PositiveIntegerField(null=True, help_text="A number that may be associated with this structure, such as a chapter or verse number; corresponds to OSIS @n attribute.")
    numerical_end   = models.PositiveIntegerField(null=True, help_text="If the structure spans multiple numerical designations, this is used")
    
    work = models.ForeignKey(Work, help_text="Must be same as start/end_*_token.work. Must not be a variant work; use the variant_bits to select for it")
    variant_bits = models.PositiveSmallIntegerField(default=0b00000001, help_text="Bitwise anded with Work.variant_bit to determine if belongs to work.")
    
    start_token = models.ForeignKey(Token, null=True, related_name='start_token_structure_set', help_text="Used to demarcate the exclusive start point for the structure; excludes any typographical marker that marks up the structure in the text, such as quotation marks. If null, then tokens should be discovered via TokenStructureItem.")
    end_token   = models.ForeignKey(Token, null=True, related_name='end_token_structure_set',   help_text="Same as start_token, but for the end.")
    
    start_marker_token = models.ForeignKey(Token, null=True, related_name='start_marker_token_structure_set', help_text="Used to demarcate the inclusive start point for the structure; marks any typographical feature used to markup the structure in the text (e.g. quotation marks).")
    end_marker_token   = models.ForeignKey(Token, null=True, related_name='end_marker_token_structure_set',   help_text="Same as start_marker_token, but for the end.")
    
    is_structure_marker = None #This boolean is set when querying via get_tokens
    
    def get_tokens(self, variant_bits = None):
        if variant_bits is None:
            variant_bits = self.variant_bits
        
        if self.start_token:
            token_start_pos = self.start_token.position
            token_end_pos = token_start_pos
            if self.end_token is not None:
                token_end_pos = self.end_token.position
            
            marker_start_pos = token_start_pos
            if self.start_marker_token is not None:
                marker_start_pos = self.start_marker_token.position
                assert(marker_start_pos <= token_start_pos)
            
            marker_end_pos = token_end_pos
            if self.start_marker_token is not None:
                marker_end_pos = self.end_marker_token.position
                assert(token_end_pos >= marker_end_pos)
            
            tokens = Token.objects.filter(
                work = self.work,
                position__gte = marker_start_pos,
                position__lte = marker_end_pos
            ).extra(where=['variant_bits & %s != 0'], params=[variant_bits])
            #if variant_bits is not None:
            #    tokens = tokens.extra(where=['variant_bits & %s != 0'], params=[variant_bits])
            
            for token in tokens:
                if token.position >= token_start_pos:
                    break
                token.is_structure_marker = True
            
            for token in reversed(tokens):
                if token.position <= token_end_pos:
                    break
                token.is_structure_marker = True
                
            return tokens
        else:
            pass
    tokens = property(get_tokens)


# This is an alternative to the above and it allows non-consecutive tokens to be
# included in a structure. But it incurs a huge amount of overhead. If
# start_token is null, then it could be assumed that a structure's tokens should
# be found via TokenStructureItem
class TokenStructureItem(models.Model):
    "Non-consecutive tokens can be assigned to a TokenStructure via this model."
    structure = models.ForeignKey(TokenStructure)
    token = models.ForeignKey(Token)
    is_marker = models.BooleanField(default=False, help_text="Whether the token is any such typographical feature which marks up the structure in the text, such as a quotation mark.")



# These relate to interlinearization; these could also be used for unification
# instead of relying on Token.unified_token
# TODO: This can also be used to associate words with a note; otherwise, start_token/end_token would be used
class TokenLinkage(models.Model):
    "Anchor point to link together multiple TokenLinkageItems"
    #work1 = models.ForeignKey(Work)
    #work2 = models.ForeignKey(Work)
    pass



class TokenLinkageItem(models.Model):
    "Tokens from different works can be linked together by instantiating TokenLinkageItems and associating them with the same TokenLinkage."
    linkage = models.ForeignKey(TokenLinkage)
    token = models.ForeignKey(Token)
    


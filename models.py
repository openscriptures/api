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
    
    variants_for_work = models.ForeignKey('self', null=True, verbose_name="Parent work that this work provides variants for")
    variant_bit = models.PositiveSmallIntegerField(default=0b00000001, help_text="The bit mask that is anded with Token.variant_bits and TokenStructure.variant_bits to query only those which belong to the work.")
    
    #Bible.en.Publisher.ABC.2010
    TYPES = (
        ('Bible', 'Bible'),
    )
    type = models.CharField(max_length=16, choices=TYPES, null=False)
    language = models.ForeignKey(Language, null=True)
    publisher = models.CharField(null=True, max_length=128)
    osis_slug = models.SlugField(max_length=16, help_text="OSIS identifier which should correspond to the abbreviation, like NIV, ESV, or KJV")
    publish_date = models.DateField(null=True, help_text="When the work was published")
    #Concatenation of previous fields:
    osis_id = models.CharField(max_length=32, choices=TYPES, null=False, db_index=True)
    
    copyright = models.TextField(null=True)
    license = models.ForeignKey(License)
    
    import_date = models.DateField(null=True, help_text="When the work was imported into the models.")
    
    #unified_work = models.ForeignKey('self', null=True, verbose_name="Work which this work has been merged into")
    
    def __unicode__(self):
        return self.title



class Token(models.Model):
    "An atomic unit of text, such as a word, punctuation mark, or whitespace line break."
    data = models.CharField(max_length=255, db_index=True)
    
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
    
    class Meta:
        ordering = ['position'] #, 'variant_number'
        #Note: This unique constraint is removed due to the fact that in MySQL, the default utf8 collation means "Και" and "καὶ" are equivalent
        #unique_together = (
        #    ('data', 'position', 'work'),
        #)
    
    def __unicode__(self):
        return self.data



class TokenStructure(models.Model):
    "Represent supra-segmental structures in the text, various markup"
    
    #Todo: Is there a better way of doing these enumerations? Integers chosen instead
    #      of a CharField to save space.
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
    variant_bits = models.PositiveSmallIntegerField(default=0b00000001, help_text="Bitwise anded with Work.variant_bit to determine if belongs to work.")
    
    start_token = models.ForeignKey(Token, related_name='start_token_structure_set', help_text="Used to demarcate the exclusive start point for the structure; excludes any typographical marker that marks up the structure in the text, such as quotation marks.")
    end_token   = models.ForeignKey(Token, related_name='end_token_structure_set',   help_text="Same as start_token, but for the end.")
    
    start_marker_token = models.ForeignKey(Token, related_name='start_marker_token_structure_set', help_text="Used to demarcate the inclusive start point for the structure; marks any typographical feature used to markup the structure in the text (e.g. quotation marks).")
    end_marker_token   = models.ForeignKey(Token, related_name='end_marker_token_structure_set',   help_text="Same as start_marker_token, but for the end.")



# These relate to interlinearization; these could also be used for unification
# instead of relying on Token.unified_token
class TokenLinkage(models.Model):
    "Anchor point to link together multiple TokenLinkageItems"
    #work1 = models.ForeignKey(Work)
    #work2 = models.ForeignKey(Work)
    pass



class TokenLinkageItem(models.Model):
    "Tokens from different works can be linked together by instantiating TokenLinkageItems and assigning them to the same TokenLinkage"
    token = models.ForeignKey(Token)


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
    variant_bit = models.IntegerField() #00000001   #CommaSeparatedIntegerField?
    
    #Bible.en.Crossway.ESV.2002
    TYPES = (
        ('Bible', 'Bible'),
        ('Mishna', 'Mishna'), #?
        ('Quran', 'Quran') #?
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
    variant_bits = models.IntegerField()
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
    #'book', 'bookGroup', 'chapter', 'verse', 'section', 'subSection', 'title', 'paragraph', 'quotation', 'questionable-1', 'questionable-2'
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
    variant_bits = models.IntegerField()
    
    start_token = models.ForeignKey(Token, related_name='start_token_structure_set')
    end_token = models.ForeignKey(Token, related_name='end_token_structure_set')
    start_marker_token = models.ForeignKey(Token, related_name='start_marker_token_structure_set')
    end_marker_token = models.ForeignKey(Token, related_name='end_marker_token_structure_set')


class TokenLinkage(models.Model):
    #work1 = models.ForeignKey(Work)
    #work2 = models.ForeignKey(Work)
    pass


class TokenLinkageItem(models.Model):
    token = models.ForeignKey(Token)


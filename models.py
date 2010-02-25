# coding: utf8 #

from django.db import models
from django.db.models import Q


OSIS_BIBLE_BOOK_CODES = (
    "Gen", "Exod", "Lev", "Num", "Deut", "Josh", "Judg", "Ruth", "1Sam", "2Sam", "1Kgs", "2Kgs", "1Chr", "2Chr", "Ezra", "Neh", "Esth", "Job", "Ps", "Prov", "Eccl", "Song", "Isa", "Jer", "Lam", "Ezek", "Dan", "Hos", "Joel", "Amos", "Obad", "Jonah", "Mic", "Nah", "Hab", "Zeph", "Hag", "Zech", "Mal",
    "Matt", "Mark", "Luke", "John", "Acts", "Rom", "1Cor", "2Cor", "Gal", "Eph", "Phil", "Col", "1Thess", "2Thess", "1Tim", "2Tim", "Titus", "Phlm", "Heb", "Jas", "1Pet", "2Pet", "1John", "2John", "3John", "Jude", "Rev",
    "Bar", "AddDan", "PrAzar", "Bel", "SgThree", "Sus", "1Esd", "2Esd", "AddEsth", "EpJer", "Jdt", "1Macc", "2Macc", "3Macc", "4Macc", "PrMan", "Sir", "Tob", "Wis"
)

OSIS_BOOK_NAMES = {
	"Gen": "Genesis",
	"Exod": "Exodus",
	"Lev": "Leviticus",
	"Num": "Numbers",
	"Deut": "Deuteronomy",
	"Josh": "Joshua",
	"Judg": "Judges",
	"Ruth": "Ruth",
	"1Sam": "1 Samuel",
	"2Sam": "2 Samuel",
	"1Kgs": "1 Kings",
	"2Kgs": "2 Kings",
	"1Chr": "1 Chronicles",
	"2Chr": "2 Chronicles",
	"Ezra": "Ezra",
	"Neh": "Nehemiah",
	"Esth": "Esther",
	"Job": "Job",
	"Ps": "Psalms",
	"Prov": "Proverbs",
	"Eccl": "Ecclesiastes",
	"Song": "Song of Solomon",
	"Isa": "Isaiah",
	"Jer": "Jeremiah",
	"Lam": "Lamentations",
	"Ezek": "Ezekiel",
	"Dan": "Daniel",
	"Hos": "Hosea",
	"Joel": "Joel",
	"Amos": "Amos",
	"Obad": "Obadiah",
	"Jonah": "Jonah",
	"Mic": "Micah",
	"Nah": "Nahum",
	"Hab": "Habakkuk",
	"Zeph": "Zephaniah",
	"Hag": "Haggai",
	"Zech": "Zechariah",
	"Mal": "Malachi",
	
	"Matt": "Matthew",
	"Mark": "Mark",
	"Luke": "Luke",
	"John": "John",
	"Acts": "Acts",
	"Rom": "Romans",
	"1Cor": "1 Corinthians",
	"2Cor": "2 Corinthians",
	"Gal": "Galatians",
	"Eph": "Ephesians",
	"Phil": "Philippians",
	"Col": "Colossians",
	"1Thess": "1 Thessalonians",
	"2Thess": "2 Thessalonians",
	"1Tim": "1 Timothy",
	"2Tim": "2 Timothy",
	"Titus": "Titus",
	"Phlm": "Philemon",
	"Heb": "Hebrews",
	"Jas": "James",
	"1Pet": "1 Peter",
	"2Pet": "2 Peter",
	"1John": "1 John",
	"2John": "2 John",
	"3John": "3 John",
	"Jude": "Jude",
	"Rev": "Revelation",
	
	"Bar": "Baruch",
	"AddDan": "Additions to Daniel",
	"PrAzar": "Prayer of Azariah",
	"Bel": "Bel and the Dragon",
	"SgThree": "Song of the Three Young Men",
	"Sus": "Susanna",
	"1Esd": "1 Esdras",
	"2Esd": "2 Esdras",
	"AddEsth": "Additions to Esther",
	"EpJer": "Epistle of Jeremiah",
	"Jdt": "Judith",
	"1Macc": "1 Maccabees",
	"2Macc": "2 Maccabees",
	"3Macc": "3 Maccabees",
	"4Macc": "4 Maccabees",
	"PrMan": "Prayer of Manasseh",
	"Sir": "Sirach/Ecclesiasticus",
	"Tob": "Tobit",
	"Wis": "Wisdom of Solomon"
}




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


class Work(models.Model):
    "Represents an OSIS work, such as the Bible or a non-biblical work such as the Qur'an or the Mishnah."
    
    title = models.CharField(max_length=255)
    abbreviation = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    source_url = models.URLField(blank=True, help_text="URL where this resource was originally obtained")
    
    variants_for_work = models.ForeignKey('self', null=True, default=None, verbose_name="Parent work that this work provides variants for")
    variant_bit = models.PositiveSmallIntegerField(default=0b00000001, help_text="The bit mask that is anded with Token.variant_bits and TokenStructure.variant_bits to query only those which belong to the work.")
    
    #Bible.en.Publisher.ABC.2010
    TYPES = (
        ('Bible', 'Bible'),
    )
    type = models.CharField(max_length=16, choices=TYPES, null=False, db_index=True)
    language = models.ForeignKey(Language, null=True, db_index=True)
    #Note: In the case of Daniel, both Hebrew and Aramaic in the book, though
    #      Hebrew is predominat; in this case, Work.language would still be 'hbo'; the
    #      language of the individual Tokens in the work can be indicated in a
    #      separate TokenMetadata model. This would allow multiple languages to be
    #      associated with a Token as there may be different opinions about what
    #      language it is!
    
    publisher = models.CharField(blank=True, max_length=128, db_index=True)
    osis_slug = models.SlugField(max_length=16, db_index=True, help_text="OSIS identifier which should correspond to the abbreviation, like NIV, ESV, or KJV")
    publish_date = models.DateField(null=True, db_index=True, help_text="When the work was published")
    #Concatenation of previous fields:
    #osis_id = models.CharField(max_length=32, choices=TYPES, null=False, db_index=True)
    def get_osis_id(self):
        _osis_id = []
        if self.type:
            _osis_id.append(self.type)
        if self.language:
            _osis_id.append(self.language.code)
        if self.osis_slug:
            _osis_id.append(self.osis_slug)
        if self.publish_date:
            _osis_id.append(self.publish_date.year)
        return ".".join(_osis_id)
    osis_id = property(get_osis_id)
    
    creator = models.TextField(blank=True)
    copyright = models.TextField(blank=True)
    license = models.ForeignKey(License, null=True)
    
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
    type = models.PositiveSmallIntegerField(choices=TYPES, default=WORD, db_index=True, help_text="A general hint as to what the token data represents")
    position = models.PositiveIntegerField(db_index=True)
    work = models.ForeignKey(Work)
    variant_bits = models.PositiveSmallIntegerField(default=0b00000001, help_text="Bitwise anded with Work.variant_bit to determine if belongs to work.")
    unified_token = models.ForeignKey('self', null=True, help_text="The token in the merged/unified work that represents this token.")
    
    #TODO: This is where internal linked data connects with the data out in the world through hyperlinks
    src_href = models.CharField(max_length=255, blank=True, help_text="XPointer to where this token came from; base URL is work.src_url")
    
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
        #...
    )
    type = models.PositiveSmallIntegerField(choices=TYPES, db_index=True)
    osis_id = models.CharField(max_length=32, blank=True, db_index=True)
    
    # title?
    # position?
    # parent?
    position = models.PositiveIntegerField(help_text="The order where this appears in the work.")
    
    numerical_start = models.PositiveIntegerField(null=True, help_text="A number that may be associated with this structure, such as a chapter or verse number; corresponds to OSIS @n attribute.")
    numerical_end   = models.PositiveIntegerField(null=True, help_text="If the structure spans multiple numerical designations, this is used")
    
    work = models.ForeignKey(Work, help_text="Must be same as start/end_*_token.work. Must not be a variant work; use the variant_bits to select for it")
    variant_bits = models.PositiveSmallIntegerField(default=0b00000001, help_text="Bitwise anded with Work.variant_bit to determine if belongs to work.")
    
    start_token = models.ForeignKey(Token, null=True, related_name='start_token_structure_set', help_text="Used to demarcate the exclusive start point for the structure; excludes any typographical marker that marks up the structure in the text, such as quotation marks. If null, then tokens should be discovered via TokenStructureItem.")
    end_token   = models.ForeignKey(Token, null=True, related_name='end_token_structure_set',   help_text="Same as start_token, but for the end.")
    
    start_marker_token = models.ForeignKey(Token, null=True, related_name='start_marker_token_structure_set', help_text="Used to demarcate the inclusive start point for the structure; marks any typographical feature used to markup the structure in the text (e.g. quotation marks).")
    end_marker_token   = models.ForeignKey(Token, null=True, related_name='end_marker_token_structure_set',   help_text="Same as start_marker_token, but for the end.")
    
    is_structure_marker = None #This boolean is set when querying via get_tokens
    
    def get_tokens(self, include_markers = True, variant_bits = None):
        if variant_bits is None:
            variant_bits = self.variant_bits
        
        # Get the tokens from a range
        if self.start_token:
            # Get start and end positions for the tokens
            start_pos = token_start_pos = self.start_token.position
            end_pos = token_end_pos = token_start_pos
            if self.end_token is not None:
                end_pos = token_end_pos = self.end_token.position
            
            # Get start position for marker
            if include_markers:
                marker_start_pos = token_start_pos
                if self.start_marker_token is not None:
                    start_pos = marker_start_pos = self.start_marker_token.position
                    assert(marker_start_pos <= token_start_pos)
                
                # Get end position for the marker
                marker_end_pos = token_end_pos
                if self.start_marker_token is not None:
                    end_pos = marker_end_pos = self.end_marker_token.position
                    assert(token_end_pos >= marker_end_pos)
            
            # Get all of the tokens between the marker start and marker end
            # and who have variant bits that match the requested variant bits
            tokens = Token.objects.filter(
                work = self.work,
                position__gte = start_pos,
                position__lte = end_pos
            ).extra(where=['variant_bits & %s != 0'], params=[variant_bits])
            #if variant_bits is not None:
            #    tokens = tokens.extra(where=['variant_bits & %s != 0'], params=[variant_bits])
            
            # Indicate which of the beginning queried tokens are markers
            for token in tokens:
                if token.position >= token_start_pos:
                    break
                token.is_structure_marker = True
            
            # Indicate which of the ending queried tokens are markers
            for token in reversed(tokens):
                if token.position <= token_end_pos:
                    break
                token.is_structure_marker = True
            
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


# This is an alternative to the above and it allows non-consecutive tokens to be
# included in a structure. But it incurs a huge amount of overhead. If
# start_token is null, then it could be assumed that a structure's tokens should
# be found via TokenStructureItem
class TokenStructureItem(models.Model):
    "Non-consecutive tokens can be assigned to a TokenStructure via this model."
    structure = models.ForeignKey(TokenStructure)
    token = models.ForeignKey(Token)
    is_marker = models.BooleanField(default=False, help_text="Whether the token is any such typographical feature which marks up the structure in the text, such as a quotation mark.")



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
    


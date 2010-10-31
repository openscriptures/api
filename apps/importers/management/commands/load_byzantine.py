#!/usr/bin/env python
# encoding: utf-8

import datetime
import os
import re
import StringIO
import unicodedata
import zipfile
import urllib

from optparse import make_option

from django.core.management.base import BaseCommand

from core import osis
from importers.management.import_helpers import abort_if_imported
from importers.management.import_helpers import close_structure
from importers.management.import_helpers import delete_work
from importers.management.import_helpers import download_resource
from texts.models import Work, Token, Structure, WorkServer
from core.models import Language, License, Server

#PUNC_CHRS = re.escape(''.join(unichr(x) for x in range(65536) if unicodedata.category(unichr(x)) == 'Po'))
PUNC_CHRS = re.escape(ur'.·,;:!?"\'')

# The followig regular epression identifies the parts of the following line:
#40N	1	1		10	Βίβλος G976 N-NSF γενέσεως G1078 N-GSF Ἰησοῦ G2424 N-GSM χριστοῦ G5547 N-GSM , υἱοῦ G5207 N-GSM Δαυίδ G1138 N-PRI , υἱοῦ G5207 N-GSM Ἀβραάμ G11 N-PRI .
LINE_PARSER = re.compile(ur"""^
        (?P<book>\d+\w+)\t+         # Unbound Bible Code
        (?P<chapter>\d+)\t+         # Chapter
        (?P<verse>\d+)\t+           # Verse
        \d+\t+                      # Ignore orderby column
        (?P<data>.*?)
    \s*$""",
    re.VERBOSE
)

# Regular expression to parse each individual word on a line (the data group from above)
# Ὃ G3739 R-ASN ἤν G1510 G5707 V-IAI-3S ἀπ' G575 PREP ἀρχῆς G746 N-GSF , ὃ G3739 R-ASN ἀκηκόαμεν G191 G5754 V-2RAI-1P-ATT , ὃ G3739 R-ASN ἑωράκαμεν G3708 G5758 V-RAI-1P-ATT τοῖς G3588 T-DPM ὀφθαλμοῖς G3788 N-DPM ἡμῶν G1473 P-1GP , ὃ G3739 R-ASN ἐθεασάμεθα G2300 G5662 V-ADI-1P , καὶ G2532 CONJ αἱ G3588 T-NPF χεῖρες G5495 N-NPF ἡμῶν G1473 P-1GP ἐψηλάφησαν G5584 G5656 V-AAI-3P περὶ G4012 PREP τοῦ G3588 T-GSM λόγου G3056 N-GSM τῆς G3588 T-GSF ζωῆς G2222 N-GSF .
TOKEN_PARSER = re.compile(ur"""
        (?P<word>\S+)\s+
        (?P<rawParsing>
            G?\d+
            (?:  \s+G?\d+  |  \s+[A-Z0-9\-:]+  )+
        )
        (?:
            \s+(?P<punctuation>[%s])
        )?
        (?:\s+ | \s*$ )
    """ % re.escape(ur""".·,;:!?"'"""),
    re.VERBOSE | re.UNICODE)

BP5_FILE = "BP05FNL.ZIP"
CCT_FILE = "BYZ05CCT.ZIP"

class Command(BaseCommand):
    args = '<Jude John ...>'
    help = 'Limits the scope of the load to just to the books specified.'

    option_list = BaseCommand.option_list + (
        make_option('--force',
            action='store_true',
            dest='force',
            default=False,
            help='Force load despite it already being loaded'),
    )
    
    def create_work(self):
        work = Work(
            title        = "Byzantine/Majority Text (2005)",
            language     = Language('grc'),
            type         = 'Bible',
            osis_slug    = 'Byzantine',
            publish_date = date(2005, 1, 1),
            import_date  = datetime.datetime.now(),
            creator      = "Maurice A. Robinson and William G. Pierpont.",
            source_url   = "http://byztxt.com/downloads.html",
            license      = License.objects.get(url="http://creativecommons.org/licenses/publicdomain/")
        )
        work.save()
        WorkServer.objects.create(
            work = work,
            server = Server.objects.get(is_self = True)
        )
        return work

################################################################################
# Text download and conversion functions
# From greek_byzantine_2005_parsed.prepare_data.py
# Developed by Tom Brazier

# Notes:
# 1. BYZ05CCT.ZIP contains AC24.CCT which is a variant of Acts 24:6-8.  The text in
#    AC.CCT, however is the same as the physical book (1st edition) so we prefer it.
# 2. BYZ05CCT.ZIP contains PA.CCT which is a variant form of the Pericope Adulterae.
#    Once again, the text in JOH.CCT is the main text in the book (the variant is
#    in the apparatus).  So we prefer JOH.CCT.
# 3. Rev 17:8 starts in different places in the BP5 text and the CCT text, although
#    the BP5 text lists the alternative starting point with parentheses.  The text
#    in the CCT file matches the physical book, so there's a tweak below to prefer it.
################################################################################

    def bp5_to_unicode(self, bp5_word):
        "Convert a word from Robinson & Pierpont's ASCII format to unicode"
        # we know about all of these character translations - anything else is an error
        table = u' ' * 65 + u'ΑΒΧΔΕΦΓΗΙ ΚΛΜΝΟΠΨΡΣΤΥΣΩΞΘΖ' + u' ' * 6 + u'αβχδεφγηι κλμνοπψρστυςωξθζ' + ' ' * 133
        res = bp5_word.translate(table)
        assert(u' ' not in res)
        return res
    
    def read_bp5_file(self, book):
        """Read a book in BP5 format from BP5_FILE and turn it into a list of chapters,
        each of which is a list of verses, each of which is a list of words, each of
        which is a tuple starting with the unicode word and followed by one or more strongs
        numbers and parsings.
    
        BP5 files contain the data for one book.  Each verse starts on a new line with
        some spaces followed by chapter and verse.  There are also other line breaks.
        Words are in a "preformatted ASCII" format, followed by strong number and then
        parsing.  More info from here: http://www.byztxt.com/downloads.html"""
    
        print("Coverting book %s from BP5" % book)
    
        bp5_zip_file = zipfile.ZipFile(BP5_FILE)
    
        # first pass, get all the words for all the verses
        chapters = []
        for line in StringIO.StringIO(bp5_zip_file.read(book + ".BP5")):
            # look for verse breaks
            match = re.match(r" +([0-9]+):([0-9]+)(.*)", line)
            if match:
                # get chapter and verse and change line to be the remainder
                chap, verse, line = (int(match.group(1)), int(match.group(2)), match.group(3))
                if chap != len(chapters):
                    chapters.append([])
                assert(chap == len(chapters))
                curr_verse = []
                chapters[-1].append(curr_verse)
                assert(verse == len(chapters[-1]))
    
            # store all words for verse (these should consist of triples of greek word, strongs number and parsing)
            words = line.strip().split()
            curr_verse += words
    
        # now iterate through all verses, translating to unicode, translating parsings and putting word components together
        clean_chapters = []
        word_re = re.compile(r"([a-zA-Z]+) *")
        number_re = re.compile(r"([0-9]+) *")
        parsing_re = re.compile(r"{([A-Z123\-]+)} *")
        verse_number_re = re.compile(r" *\([0-9]+:[0-9]+\) *")
        for chapter in chapters:
            # work around for different starting points of Rev 17:8 (see notes at the top)
            if book == "RE" and chapter is chapters[16]:
                pos = chapter[6].index("(17:8)")
                chapter[7] = chapter[6][pos + 1:] + chapter[7]
                chapter[6] = chapter[6][:pos]
    
            clean_chapter = []
            for verse in chapter:
                clean_verse = []
                verse = ' '.join(verse)
                # marginal apparatus notes are delimited by pipe characters, strip the variants
                verse = re.sub(r"\| ([^\|]*) \|[^\|]*\|", r'\1', verse)
                while verse:
                    # occasionally (eg. Matt 23:13) an alternative verse number is inserted in brackets, ignore it
                    verse_number_match = verse_number_re.match(verse)
                    if verse_number_match: verse = verse[verse_number_match.end():]
                    # match word
                    word = []
                    word_match = word_re.match(verse)
                    assert(word_match)
                    verse = verse[word_match.end():]
                    word.append(self.bp5_to_unicode(word_match.group(1)))
                    while True:
                        number_match = number_re.match(verse)
                        parsing_match = parsing_re.match(verse)
                        if not number_match and not parsing_match: break
                        if number_match:
                            verse = verse[number_match.end():]
                            word.append("G" + number_match.group(1))
                        if parsing_match:
                            verse = verse[parsing_match.end():]
                            word.append(parsing_match.group(1))
                    clean_verse.append(tuple(word))
                clean_chapter.append(clean_verse)
            clean_chapters.append(clean_chapter)
    
        return clean_chapters
    
    def cct_to_unicode(self, bp5_word):
        """Convert a word from Robinson & Pierpont's modified betacode format to unicode, and
        return it along with a plain old un-accented, lowercase version for later comparison with BP5"""
    
        # we know about all of these character translations - anything else is an error
        table = u' ' * 39 + u"'() +, ./          :;     ΑΒΞΔΕΦΓΗΙ ΚΛΜΝΟΠΘΡΣΤΥ ΩΧΨΖ \ ^  αβξδεφγηι κλμνοπθρστυ ωχψζ |   " + u' ' * 128
        res1 = bp5_word.translate(table)
        res2 = re.sub("[^a-z,.:;]", '', bp5_word.lower()).translate(table)
        assert(u' ' not in res1)
    
        # convert final sigmas
        if res1[-1] == u'σ': res1 = res1[0:-1] + u'ς'
        if res2[-1] == u'σ': res2 = res2[0:-1] + u'ς'
    
        # move initial accents to after the first letter so they're positioned like all other accents
        res1 = re.sub(r"^([\(\)/\\\^\+\|]*)(.)", "\\2\\1", res1)
    
        # iterate through all accents
        accent_list = []
        for match in re.finditer(r"(.)([\(\)/\\\^\+\|]+)", res1):
            letter, annotations = match.groups()
            accent_list.append((match.start(), match.end(), letter, annotations))
    
        for match_start, match_end, letter, annotations in reversed(accent_list):
            assert(letter in u'ΑΕΗΙΟΡΥΩαεηιορυω')
    
            # parse breathings, accents, etc.
            smooth_breathing = ")" in annotations
            rough_breathing = "(" in annotations
            assert(smooth_breathing + rough_breathing <= 1)
            diaeresis = "+" in annotations
            iota_subscript = "|" in annotations
            acute_accent = "/" in annotations
            grave_accent = "\\" in annotations
            circumflex_accent = "^" in annotations
            assert(acute_accent + grave_accent + circumflex_accent <= 1)
    
            # do some useful preprocessing of the letter
            is_upper_case = letter in u'ΑΕΗΙΟΡΥΩ'
            lower_case = {u'Α':u'α', u'Ε':u'ε', u'Η':u'η', u'Ι':u'ι', u'Ο':u'ο', u'Υ':u'υ', u'Ω':u'ω'}.get(letter, letter)
    
            # rho is easy
            if letter in u'Ρρ':
                assert(annotations == "(")
                res1 = res1[:match_start] + {u'Ρ':u'Ῥ', u'ρ':u'ῥ'}[letter] + res1[match_end:]
                continue
    
            # diaeresis is easy
            if diaeresis:
                offset = acute_accent * 1 + circumflex_accent * 5
                letter = {u'ι':u'ῒ', u'υ':u'ῢ'}[letter]
                letter = unichr(ord(letter) + offset)
                res1 = res1[:match_start] + letter + res1[match_end:]
                continue
    
            # unicode has a very nice tabular encoding for vowels with breathings
            if smooth_breathing or rough_breathing:
                offset = rough_breathing * 1 + grave_accent * 2 + acute_accent * 4 + circumflex_accent * 4 + is_upper_case * 8
                if iota_subscript:
                    letter = {u'α':u'ᾀ', u'η':u'ᾐ', u'ω':u'ᾠ'}[lower_case]
                else:
                    letter = {u'α':u'ἀ', u'ε':u'ἐ', u'η':u'ἠ', u'ι':u'ἰ', u'ο':u'ὀ', u'υ':u'ὐ', u'ω':u'ὠ'}[lower_case]
                letter = unichr(ord(letter) + offset)
                res1 = res1[:match_start] + letter + res1[match_end:]
                continue
    
            # now we can clean up the remaining iota subscripts
            if iota_subscript and not is_upper_case:
                offset = grave_accent * -1 + acute_accent * 1 + circumflex_accent * 4
                letter = {u'α':u'ᾳ', u'η':u'ῃ', u'ω':u'ῳ'}[letter]
                letter = unichr(ord(letter) + offset)
                res1 = res1[:match_start] + letter + res1[match_end:]
                continue
    
            # now we can clean up the remaining lower-case acutes and graves
            if (grave_accent or acute_accent) and not is_upper_case:
                offset = acute_accent * 1
                offset += {u'α':0, u'ε':2, u'η':4, u'ι':6, u'ο':8, u'υ':10, u'ω':12}[lower_case]
                letter = unichr(ord(u'ὰ') + offset)
                res1 = res1[:match_start] + letter + res1[match_end:]
                continue
    
            # and the remaining circumflexes and upper-case acutes and graves
            if circumflex_accent and not is_upper_case or (grave_accent or acute_accent) and is_upper_case:
                assert(letter not in u'εο')
                offset = grave_accent * 4 + acute_accent * 5
                offset += {u'α':0, u'ε':14, u'η':16, u'ι':32, u'ο':62, u'υ':48, u'ω':64}[lower_case]
                letter = unichr(ord(u'ᾶ') + offset)
                res1 = res1[:match_start] + letter + res1[match_end:]
                continue
    
            # we ought to have covered all cases now
            assert(False)
    
        # make sure we got all the accents
        assert(not re.match(u'.*[\(\)/\\\^\+\|]', res1))
        return (res1, res2)
    
    def read_cct_file(self, book):
        """Read a book in CCT format from CCT_FILE and turn it into a list of chapters,
        each of which is a list of verses, each of which is a list of accented words and
        punctuation marks.
    
        CCT files contain the data for one book.  There is exactly one line per verse.
        Words are in a a modified betacode format.  More info from here:
        http://www.byztxt.com/downloads.html"""
    
        print("Coverting book %s from CCT" % book)
    
        cct_zip_file = zipfile.ZipFile(CCT_FILE)
    
        # run through the lines, building chapters
        chapters = []
        for line in StringIO.StringIO(cct_zip_file.read(book + ".CCT")):
            # ignore comment lines
            if line[0] == "#": continue
    
            # strip the variant readings and paragraph breaks
            line = re.sub(r" *\{[^\}]*} *", ' ', line)
    
            # strip hyphens from the text
            line = re.sub(r" *- *", ' ', line)
    
            # every line is a new verse, so get the chapter and verse numbers
            match = re.match(r" +([0-9]+):([0-9]+)(.*)", line)
            assert(match)
            chap, verse, line = (int(match.group(1)), int(match.group(2)), match.group(3))
    
            # build the verse
            line = re.sub(r"([,.:;])", r" \1", line)
            curr_verse = [self.cct_to_unicode(word) for word in line.strip().split()]
    
            # append chapters and verses
            if chap != len(chapters):
                chapters.append([])
            assert(chap == len(chapters))
            chapters[-1].append(curr_verse)
            assert(verse == len(chapters[-1]))
    
        return chapters

    def prepare_text(self):
        book_names = (
            "MT", "MR", "LU", "JOH", "AC", "RO", "1CO", "2CO", "GA", "EPH", "PHP", "COL", "1TH", "2TH",
            "1TI", "2TI", "TIT", "PHM", "HEB", "JAS", "1PE", "2PE", "1JO", "2JO", "3JO", "JUDE", "RE", 
        )


        
        if(not os.path.exists('BP05FNL.ZIP')):
            print("Downloading BP05FNL.ZIP")
            urllib.urlretrieve("http://koti.24.fi/jusalak/GreekNT/BP05FNL.ZIP", "BP05FNL.ZIP")
        
        if(not os.path.exists('BYZ05CCT.ZIP')):
            print("Downloading BYZ05CCT.ZIP")
            urllib.urlretrieve("http://koti.24.fi/jusalak/GreekNT/BYZ05CCT.ZIP", "BYZ05CCT.ZIP")
        
        books = []
        for book_name in book_names:
            bp5_chapters = self.read_bp5_file(book_name)
            print bp5_chapters[0][0]
            print ' '.join(word[0] for word in bp5_chapters[0][0])
            cct_chapters = self.read_cct_file(book_name)
            print ' '.join(word[1] for word in cct_chapters[0][0])
            assert(len(bp5_chapters) == len(cct_chapters))
            books.append((bp5_chapters, cct_chapters))
        
        # generate output
        print("Generating output files")
        outfile_plain = file("greek_byzantine_2005_parsed_utf8.txt", "wb")
        outfile_plain.write(
        """#name\tGreek NT: Byzantine/Majority Text (2005) [Parsed]
        #filetype\tUnmapped-BCVS
        #copyright\tSee http://www.byztxt.com/
        #abbreviation\t
        #language\tgko
        #note\t
        #columns\torig_book_index\torig_chapter\torig_verse\torder_by\ttext
        """)
        
        outfile_punc = file("greek_byzantine_2005_parsed_punc_utf8.txt", "wb")
        outfile_punc.write(
        """#name\tGreek NT: Byzantine/Majority Text (2005) [Parsed with punctuation, accents and breathings]
        #filetype\tUnmapped-BCVS
        #copyright\tSee http://www.byztxt.com/
        #abbreviation\t
        #language\tgko
        #note\t
        #columns\torig_book_index\torig_chapter\torig_verse\torder_by\ttext
        """)
        
        ordering = 0
        for i_book in range(len(books)):
            print("Book: %s" % book_names[i_book])
            bp5_chapters, cct_chapters = books[i_book]
            for i_chap in range(len(bp5_chapters)):
                bp5_chapter = bp5_chapters[i_chap]
                cct_chapter = cct_chapters[i_chap]
                assert(len(bp5_chapter) == len(cct_chapter))
                for i_verse in range(len(bp5_chapter)):
                    bp5_verse = bp5_chapter[i_verse]
                    cct_verse = cct_chapter[i_verse]
        
                    # run through the verse building the output line
                    out_words_punc = []
                    out_words_plain = []
                    i_bp5_word = i_cct_word = 0
                    while i_bp5_word < len(bp5_verse) or i_cct_word < len(cct_verse):
                        if i_bp5_word < len(bp5_verse): bp5_word = bp5_verse[i_bp5_word]
                        if not i_cct_word < len(cct_verse): print i_chap, i_verse, i_cct_word, i_bp5_word, len(cct_verse), len(bp5_verse)
                        cct_word = cct_verse[i_cct_word]
                        if cct_word[0] in ",.:;":
                            out_words_punc.append(cct_word[0])
                            i_cct_word += 1
                        else:
                            # ensure that we're in sync, i.e. that the unadorned CCT word is the same as the BP5 word
                            assert(cct_word[1] == bp5_word[0])
                            out_words_punc.append(cct_word[0])
                            out_words_punc += bp5_word[1:]
                            out_words_plain.append(cct_word[1])
                            out_words_plain += bp5_word[1:]
                            i_bp5_word += 1
                            i_cct_word += 1
                    ordering += 10
                    out_line = u"%dN\t%d\t%d\t\t%d\t" % (i_book + 40, i_chap + 1, i_verse + 1, ordering)
                    out_line += u"%s\n" % u' '.join(out_words_plain)
                    outfile_plain.write(out_line.encode('utf8'))
        
                    out_line = u"%dN\t%d\t%d\t\t%d\t" % (i_book + 40, i_chap + 1, i_verse + 1, ordering)
                    out_line += u"%s\n" % u' '.join(out_words_punc)
                    outfile_punc.write(out_line.encode('utf8'))
        
        del(outfile_plain)
        del(outfile_punc)

    def handle(self, *args, **options):
        # Abort if MS has already been added (or --force not supplied)
        #TODO figure out importance of "WORK1_ID" to this function
        abort_if_imported(WORK1_ID, options["force"])

        # Download the source file
        if(not os.path.exists('greek_byzantine_2005_parsed_punc_utf8.txt')):
            self.prepare_texts()

        # Create the work objects
        work = self.create_work()

        # Get the subset of OSIS book codes provided on command line
        limited_book_codes = []
        for arg in args:
            id_parts = arg.split(".")
            if id_parts[0] in osis.BOOK_ORDERS["Bible"]["KJV"]:
                limited_book_codes.append(id_parts[0])
        book_codes = osis.BOOK_ORDERS["Bible"]["KJV"]
        if len(limited_book_codes) > 0:
			book_codes = limited_book_codes

        tokenCount = 1
        structCount = 1
        #_zip = zipfile.ZipFile(os.path.basename(SOURCE_URL))
        for book_code in book_codes:
            if not BOOK_FILENAME_LOOKUP.has_key(book_code):
                continue

            print("Book: %s" % osis.BOOK_NAMES["Bible"][book_code])
            
            # Set up the book ref
            structs = {}
            structs[Structure.BOOK] = Structure(
                work = work1,
                type = Structure.BOOK,
                osis_id = book_code,
                position = structCount,
                numerical_start = book_codes.index(book_code),
                variant_bits = WORK2_VARIANT_BIT | WORK1_VARIANT_BIT,
                # Can't use source_url because of data conversion issue
                #source_url = "zip:" + SOURCE_URL + "!/Tischendorf-2.5/Unicode/" + BOOK_FILENAME_LOOKUP[book_code]
                #title = osis.BOOK_NAMES["Bible"][book_code]
            )
            
            structCount += 1
            bookTokens = []
            current_chapter = None
            current_verse = None
            lineNumber = -1



### ORIGINAL FILE BELOW ###



# First step is to fetch the data from the server via script by Tom Brazier which converts the source from Betacode to Unicode and the Unbound Bible file format
# TODO Change this to a class or function instead of executing external script
#if(not os.path.exists('greek_byzantine_2005_parsed_punc_utf8.txt')):
    #execfile('greek_byzantine_2005_parsed.prepare_data.py')

#import_helpers.delete_work(msID)


## The followig regular epression identifies the parts of the following line:
##40N	1	1		10	Βίβλος G976 N-NSF γενέσεως G1078 N-GSF Ἰησοῦ G2424 N-GSM χριστοῦ G5547 N-GSM , υἱοῦ G5207 N-GSM Δαυίδ G1138 N-PRI , υἱοῦ G5207 N-GSM Ἀβραάμ G11 N-PRI .
#lineParser = re.compile(ur"""^
        #(?P<book>\d+\w+)\t+         # Unbound Bible Code
        #(?P<chapter>\d+)\t+         # Chapter
        #(?P<verse>\d+)\t+           # Verse
        #\d+\t+                      # Ignore orderby column
        #(?P<data>.*?)
    #\s*$""",
    #re.VERBOSE
#)

## Regular expression to parse each individual word on a line (the data group from above)
## Ὃ G3739 R-ASN ἤν G1510 G5707 V-IAI-3S ἀπ' G575 PREP ἀρχῆς G746 N-GSF , ὃ G3739 R-ASN ἀκηκόαμεν G191 G5754 V-2RAI-1P-ATT , ὃ G3739 R-ASN ἑωράκαμεν G3708 G5758 V-RAI-1P-ATT τοῖς G3588 T-DPM ὀφθαλμοῖς G3788 N-DPM ἡμῶν G1473 P-1GP , ὃ G3739 R-ASN ἐθεασάμεθα G2300 G5662 V-ADI-1P , καὶ G2532 CONJ αἱ G3588 T-NPF χεῖρες G5495 N-NPF ἡμῶν G1473 P-1GP ἐψηλάφησαν G5584 G5656 V-AAI-3P περὶ G4012 PREP τοῦ G3588 T-GSM λόγου G3056 N-GSM τῆς G3588 T-GSF ζωῆς G2222 N-GSF .
#tokenParser = re.compile(ur"""
        #(?P<word>\S+)\s+
        #(?P<rawParsing>
            #G?\d+
            #(?:  \s+G?\d+  |  \s+[A-Z0-9\-:]+  )+
        #)
        #(?:
            #\s+(?P<punctuation>[%s])
        #)?
        #(?:\s+ | \s*$ )
    #""" % re.escape(ur""".·,;:!?"'"""),
    #re.VERBOSE | re.UNICODE)

#bookRefs = []
#chapterRefs = []
#verseRefs = []
#tokens = []
#previousTokens = []
#tokenPosition = 0

#f = open('greek_byzantine_2005_parsed_punc_utf8.txt', 'r')
#for verseLine in f:
    #if(verseLine.startswith('#')):
        #continue
    #verseLine = unicodedata.normalize("NFC", unicode(verseLine, 'utf-8'))
    #verseInfo = lineParser.match(verseLine)
    #if(not verseInfo):
        #raise Exception("Parse error on line: " + verseLine)
    #if(not verseInfo.group('data') or UNBOUND_CODE_TO_OSIS_CODE[verseInfo.group('book')] not in OSIS_BIBLE_BOOK_CODES):
        #continue
    #meta = verseInfo.groupdict()

    ## Create book ref if it doesn't exist
    #if(not len(bookRefs) or bookRefs[-1].osis_id != UNBOUND_CODE_TO_OSIS_CODE[meta['book']]):
        #print UNBOUND_CODE_TO_OSIS_CODE[meta['book']]
        
        ## Reset tokens
        #previousTokens = tokens
        #tokens = []
        
        ## Close book and chapter refs
        #if(len(previousTokens)):
            #bookRefs[-1].end_token = previousTokens[-1]
            #bookRefs[-1].save()
            #chapterRefs[-1].end_token = previousTokens[-1]
            #chapterRefs[-1].save()
        #chapterRefs = []
        #verseRefs = []
        
        ## Set up the book ref
        #bookRef = Ref(
            #work = msWork,
            #type = Ref.BOOK,
            #osis_id = UNBOUND_CODE_TO_OSIS_CODE[meta['book']],
            #position = len(bookRefs),
            #title = OSIS_BOOK_NAMES[UNBOUND_CODE_TO_OSIS_CODE[meta['book']]]
        #)
        ##bookRef.save()
        ##bookRefs.append(bookRef)
        
    ## So here we need to have tokenParser match the entire line
    #pos = 0
    #verseTokens = []
    #while(pos < len(meta['data'])):
        #tokenMatch = tokenParser.match(meta['data'], pos)
        #if(not tokenMatch):
            #print "%s %02d %02d" % (meta['book'], int(meta['chapter']), int(meta['verse']))
            #print "Unable to parse at position " + str(pos) + ": " + meta['data']
            #raise Exception("Unable to parse at position " + str(pos) + ": " + meta['data'])
        
        ## Insert token
        #token = Token(
            #data     = tokenMatch.group('word'),
            #type     = Token.WORD,
            #work     = msWork,
            #position = tokenPosition
        #)
        #tokenPosition = tokenPosition + 1
        #token.save()
        #tokens.append(token)
        #verseTokens.append(token)
        
        ## Insert punctuation
        #if(tokenMatch.group('punctuation')):
            #token = Token(
                #data     = tokenMatch.group('punctuation'),
                #type     = Token.PUNCTUATION,
                #work     = msWork,
                #position = tokenPosition
            #)
            #tokenPosition = tokenPosition + 1
            #token.save()
            #tokens.append(token)
            #verseTokens.append(token)
        
        ## Token Parsing
        ##strongs = [tokenMatch.group('strongs1')]
        ##if(tokenMatch.group('strongs2')):
        ##    strongs.append(tokenMatch.group('strongs2'))
        #parsing = TokenParsing(
            #token = token,
            #raw = tokenMatch.group("rawParsing"),
            ##parse = tokenMatch.group('parsing'),
            ##strongs = ";".join(strongs),
            #language = Language('grc'),
            #work = msWork
        #)
        #parsing.save()
        
        ## Make this token the first in the book ref, and set the first token in the book
        #if len(tokens) == 1:
            #bookRef.start_token = tokens[0]
            #bookRef.save()
            #bookRefs.append(bookRef)
        
        ## Set up the Chapter ref
        #if(not len(chapterRefs) or chapterRefs[-1].numerical_start != meta['chapter']):
            #if(len(chapterRefs)):
                #chapterRefs[-1].end_token = tokens[-2]
                #chapterRefs[-1].save()
            #chapterRef = Ref(
                #work = msWork,
                #type = Ref.CHAPTER,
                #osis_id = ("%s.%s" % (bookRefs[-1].osis_id, meta['chapter'])),
                #position = len(chapterRefs),
                #parent = bookRefs[-1],
                #numerical_start = meta['chapter'],
                #start_token = tokens[-1]
            #)
            #chapterRef.save()
            #chapterRefs.append(chapterRef)
        
        #pos = tokenMatch.end()
        
    ## Create verse ref
    #verseRef = Ref(
        #work = msWork,
        #type = Ref.VERSE,
        #osis_id = ("%s.%s.%s" % (bookRefs[-1].osis_id, meta['chapter'], meta['verse'])),
        #position = len(verseRefs),
        #parent = chapterRefs[-1],
        #numerical_start = meta['verse'],
        #start_token = verseTokens[0],
        #end_token = verseTokens[-1]
    #)
    #verseRef.save()
    #verseRefs.append(verseRef)

##Save all books, chapters
#bookRefs[-1].end_token = tokens[-1]
#bookRefs[-1].save()
#chapterRefs[-1].end_token = tokens[-1]
#for chapterRef in chapterRefs:
    #chapterRef.save()


#f.close()

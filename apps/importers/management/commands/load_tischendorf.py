# encoding: utf-8

# NOTICE: We need to do the same thing with Tischendorf that we did with TNT: there is a corrected edition
# - One word per line
# - Space-separated fields (except for the last two)
# - - fields:
#   0. Book (corresponds to the filename, which is the Online Bible standard)
#   1. Chapter:Verse.word-within-verse
#   2. Pagraph break ("P") / Chapter break ("C") / No break (".") (see
#      below)
#   3. The text as it is written in the printed Tischendorf (Kethiv)
#   4. The text as the editor thinks it should have been (Qere)
#   5. The morphological tag (following the Qere)
#   6. The Strong's number (following the Qere)
#   7. The lemma in two versions:
#     7.a The first version, which corresponds to The NEW Strong's
#       Complete Dictionary of Bible Words.
#     7.b Followed by the string " ! "
#     7.c Then the second version, which corresponds to Friberg, Friberg
#       and Miller's ANLEX.
#     There may be several words in each lemma.
# 
# All Strong's numbers are single numbers with 1,2,3, or 4 digits.
# 
# The third column (designated "2." above) has precisely one of three
# values:
# 
# - "." : No break occurs
# - "P" : A paragraph break occurs
# - "C" : A chapter break occurs
# 
# Most paragraph breaks occur on a verse boundary, but not all paragraph
# breaks do.
# 
# A program counting the "C"s can rely on them to count the chapters,
# i.e., even if a chapter break occurs in a verse which belongs to
# chapter X, that means that Tischendorf thought that that verse belongs
# to chapter X+1.  This occurs, for example, in Revelation 12:18, where
# the chapter break occurs in chapter 12, meaning that verse 12:18 needs
# to be shown with chapter 13.
#
# I cannot believe Python doesn't have this built in
#    def grep(regexp,list):
#        "Grep from http://casa.colorado.edu/~ginsbura/pygrep.htm"
#        expr = re.compile(regexp)
#        results = []
#        for text in list:
#            match = expr.search(text)
#            if match != None:
#                results.append(match.string)
#        return results


# Standard library imports
import datetime
from optparse import make_option
import os
import re
import StringIO
import unicodedata
import zipfile

# Django imports
from django.core.management.base import BaseCommand

# Opensccriptures imports
from core import osis
from apps.importers.import_helpers import OpenScripturesImport
from apps.texts.models import Work, Token, Structure, WorkServer
from apps.core.models import Language, License, Server


# TODO: Some of this might be better defined as SETTING
SOURCE_URL = "http://files.morphgnt.org/tischendorf/Tischendorf-2.6.zip"
# No more hard-coding work_ids in importers
#WORK_ID = 1

BOOK_FILENAME_LOOKUP = {
	'Matt'   : "MT.txt"   ,
	'Mark'   : "MR.txt"   ,
	'Luke'   : "LU.txt"   ,
	'John'   : "JOH.txt"  ,
	'Acts'   : "AC.txt"   ,
	'Rom'    : "RO.txt"   ,
	'1Cor'   : "1CO.txt"  ,
	'2Cor'   : "2CO.txt"  ,
	'Gal'    : "GA.txt"   ,
	'Eph'    : "EPH.txt"  ,
	'Phil'   : "PHP.txt"  ,
	'Col'    : "COL.txt"  ,
	'1Thess' : "1TH.txt"  ,
	'2Thess' : "2TH.txt"  ,
	'1Tim'   : "1TI.txt"  ,
	'2Tim'   : "2TI.txt"  ,
	'Titus'  : "TIT.txt"  ,
	'Phlm'   : "PHM.txt"  ,
	'Heb'    : "HEB.txt"  ,
	'Jas'    : "JAS.txt"  ,
	'1Pet'   : "1PE.txt"  ,
	'2Pet'   : "2PE.txt"  ,
	'1John'  : "1JO.txt"  ,
	'2John'  : "2JO.txt"  ,
	'3John'  : "3JO.txt"  ,
	'Jude'   : "JUDE.txt" ,
	'Rev'    : "RE.txt"   ,
}

#PUNC_CHRS = re.escape(''.join(unichr(x) for x in range(65536) if unicodedata.category(unichr(x)) == 'Po'))
PUNC_CHRS = re.escape(ur'.·,;:!?"\'')
LINE_PARSER = re.compile(ur"""^
        (?P<book>\S+)\s+            # Book (corresponds to the filename, which is the Online Bible standard)
        (?P<chapter>\d+):           # Chapter
        (?P<verse>\d+)\.            # Verse
        (?P<position>\d+)\s+        # word-within-verse
        (?P<break>\S)\s+            # Pagraph break ("P") / Chapter break ("C") / No break (".")
        (?P<kethivStartBracket>\[)?
        (?P<kethiv>\S+?)            # The text as it is written in the printed Tischendorf (Kethiv)
        (?P<kethivPunc>[%s])?       # Kethiv punctuation
        (?P<kethivEndBracket>\])?\s+
    (?P<rawParsing>
        (?P<qereStartBracket>\[)?
        (?P<qere>\S+?)              # The text as the editor thinks it should have been (Qere)
        (?P<qerePunc>  [%s])?       # Qere punctuation
        (?P<qereEndBracket>\])?\s+
        (?P<morph>\S+)\s+           # The morphological tag (following the Qere)
        (?P<strongsNumber>\d+)\s+   # The Strong's number (following the Qere)
        (?P<strongsLemma>.+?)       # Lemma which corresponds to The NEW Strong's Complete Dictionary of Bible Words. (There may be several words in each lemma.)
        \s+!\s+                     # A " ! " separates the lemmas
        (?P<anlexLemma>.+?)         # Lemma which corresponds to Friberg, Friberg and Miller's ANLEX. (There may be several words in each lemma.)
    )
    \s*$""" % (PUNC_CHRS, PUNC_CHRS),
    re.VERBOSE
)

tempId = 0

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


    def handle(self, *args, **options):
        importer = OpenScripturesImport()
        
        # Abort if MS has already been added (or --force not supplied)
        importer.abort_if_imported("Tischendorf", options["force"])

        # Download the source file
        importer.download_resource(SOURCE_URL)

        # Create Works
        # Delete existing works
        if len(Work.objects.filter(osis_slug="Tischendorf")) > 0:
            importer.delete_work(Work.objects.get(osis_slug="Tischendorf"))
        
        # Work for Qere edition (Kethiv is base text)
        importer.work1 = Work(
            title        = "Tischendorf 8th ed. v2.6 Qere (Corrected)",
            language     = Language('grc'),
            type         = 'Bible',
            osis_slug    = 'Tischendorf',
            publish_date = datetime.date(2010, 7, 4),
            import_date  = datetime.datetime.now(),
            #variant_bit  = WORK2_VARIANT_BIT,
            #variants_for_work = work1,
            creator      = "<a href='http://en.wikipedia.org/wiki/Constantin_von_Tischendorf' title='Constantin von Tischendorf @ Wikipedia'>Constantin von Tischendorf</a>. Based on G. Clint Yale's Tischendorf text and on Dr. Maurice A. Robinson's Public Domain Westcott-Hort text. Edited by <a href='http://www.hum.aau.dk/~ulrikp/'>Ulrik Sandborg-Petersen</a>.",
            source_url   = SOURCE_URL,
            license      = License.objects.get(url="http://creativecommons.org/licenses/publicdomain/")
        )
        importer.work1.save()
        WorkServer.objects.create(
            work = importer.work1,
            server = Server.objects.get(is_self = True)
        )

        # Get the subset of OSIS book codes provided on command line
        limited_book_codes = []
        for arg in args:
            id_parts = arg.split(".")
            if id_parts[0] in osis.BOOK_ORDERS["Bible"]["KJV"]:
                limited_book_codes.append(id_parts[0])
        importer.book_codes = osis.BOOK_ORDERS["Bible"]["KJV"]
        if len(limited_book_codes) > 0:
            importer.book_codes = limited_book_codes

        # Read each of the Book files
        _zip = zipfile.ZipFile(os.path.basename(SOURCE_URL))
        for book_code in importer.book_codes:
            if not BOOK_FILENAME_LOOKUP.has_key(book_code):
                continue

            importer.current_book = book_code
            importer.create_book_struct()
            
            lineNumber = -1

            importer.create_paragraph()

            for line in StringIO.StringIO(_zip.read("Tischendorf-2.6/Unicode/" + BOOK_FILENAME_LOOKUP[book_code])):
                in_paragraph = 0
                lineNumber += 1
                lineMatches = LINE_PARSER.match(unicodedata.normalize("NFC", unicode(line, 'utf-8')))
                if lineMatches is None:
                    print(" -- Warning: Unable to parse line: %s" % line) 
                    continue

                # Skip verses we're not importing right now
                #verse_osisid = book_code + "." + lineMatches.group('chapter') + "." + lineMatches.group('verse')
                #if len(limited_osis_ids) and len(grep(verse_osisid, limited_osis_ids)) != 0:
                #    continue

                # New Chapter start
                if lineMatches.group('chapter') != importer.current_chapter:
                    # End the previous chapter
                    importer.close_structure('chapter')

                    # Start the next chapter
                    importer.current_chapter = lineMatches.group('chapter')
                    importer.create_chapter_struct()
                    
                # New Verse start
                if lineMatches.group('verse') != importer.current_verse:
                    # End the previous verse
                    importer.close_structure('verse')

                    # Start the next verse
                    importer.current_verse = lineMatches.group('verse')
                    importer.create_verse_struct()

                # End paragraph
                if lineMatches.group('break') == 'P':
                    importer.create_paragraph()
                    in_paragraph = 1

                if not in_paragraph and len(importer.bookTokens) > 0:
                    importer.create_whitespace_token()


                #assert(lineMatches.group('kethivPunc') == lineMatches.group('qerePunc'))
                #assert(lineMatches.group('kethivStartBracket') == lineMatches.group('qereStartBracket'))
                #assert(lineMatches.group('kethivEndBracket') == lineMatches.group('qereEndBracket'))

                #if string.find(line, '[') != -1 or string.find(line, ']') != -1 or lineMatches.group('kethiv') != lineMatches.group('qere'):
                #    print line
                #continue


                # Open UNCERTAIN1 bracket
                if lineMatches.group("qereStartBracket"):
                    importer.create_uncertain()

                importer.create_token(lineMatches.group('qere'))
                # Make sure that structures only start on words
                importer.link_start_tokens()



                # Make this token the start of the UNCERTAIN structure
                if lineMatches.group('qereStartBracket'):
                    importer.structs['doubted'].start_token = bookTokens[-1]

                # Qere token
                #if lineMatches.group('kethiv') != lineMatches.group('qere'):
                #    print("%s != %s" % (lineMatches.group('kethiv'), lineMatches.group('qere')))
                #    token_work2 = Token(
                #        id       = str(tokenCount),
                #        data     = lineMatches.group('qere'),
                #        type     = Token.WORD,
                #        work     = work,
                #        position = tokenCount,   #token_work1.position #should this be the same!?
                #        variant_bits = WORK2_VARIANT_BIT,
                #        relative_source_url = "#line(%d)" % lineNumber
                #        # What will happen with range?? end_token = work1, but then work2?
                #        # Having two tokens at the same position could mean that they are
                #        #  co-variants at that one spot. But then we can't reliably get
                #        #  tokens by a range? Also, the position can indicate transposition?
                #    )
                #    tokenCount += 1
                #    token_work2.save()
                #    lineTokens.append(token_work2)

                # Punctuation token
                #assert(lineMatches.group('kethivPunc') == lineMatches.group('qerePunc'))
                if lineMatches.group('qerePunc'):
                    importer.create_punct_token(lineMatches.group('qerePunc'))

                # Close UNCERTAIN1 bracket
                #assert(lineMatches.group('kethivEndBracket') == lineMatches.group('qereEndBracket'))
                if lineMatches.group('qereEndBracket'):
                    assert(structs.has_key('doubted'))
                    print("### CLOSE BRACKET")

                    importer.structs['doubted'].end_token = bookTokens[-1]

                    # Make end_marker for UNCERTAIN1
                    importer.create_punct_token("]")
                    # Close the UNCERTAIN1 structure
                    importer.structs['doubted'].end_marker = bookTokens[-1]
                    importer.close_structure('doubted')
                

            for structElement in importer.structs.keys():
                importer.close_structure(structElement)

            importer.bookTokens = []

        print("structCount: %s" % str(importer.structCount))
        print("tokenCount:  %s" % str(importer.tokenCount))

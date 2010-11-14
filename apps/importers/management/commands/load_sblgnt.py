# encoding: utf-8
#
# OpenScriptures importer for the SBL Greek New Testament Tex
# http://www.sblgnt.com/

import datetime
import os
import re
import StringIO
import unicodedata
import xml.sax
import zipfile

from optparse import make_option

from django.core.management.base import BaseCommand

from core import osis
from importers.management.import_helpers import abort_if_imported
from importers.management.import_helpers import close_structure
from importers.management.import_helpers import delete_work
from importers.management.import_helpers import download_resource
from texts.models import Work, Token, Structure, WorkServer
from core.models import Language, License, Server


# TODO: Some of this might be better defined as SETTING
SOURCE_URL = "http://sblgnt.com/download/SBLGNTxml.zip"

WORK1_ID = 3 # SBLGNT
WORK1_VARIANT_BIT = 0b00000001
# SBL GNT has an apparatus, but no variants
#WORK2_ID = 4 # Tischendorf Qere
#WORK2_VARIANT_BIT = 0b00000010

BOOK_ID_LOOKUP = {
	'Matt'   : "Mt"   ,
	'Mark'   : "Mk"   ,
	'Luke'   : "Lu"   ,
	'John'   : "Jn"  ,
	'Acts'   : "Ac"   ,
	'Rom'    : "Ro"   ,
	'1Cor'   : "1Co"  ,
	'2Cor'   : "2Co"  ,
	'Gal'    : "Gal"   ,
	'Eph'    : "Eph."  ,
	'Phil'   : "Php"  ,
	'Col'    : "Col"  ,
	'1Thess' : "1Th"  ,
	'2Thess' : "2Th"  ,
	'1Tim'   : "1Tim"  ,
	'2Tim'   : "2Tim"  ,
	'Titus'  : "Tit"  ,
	'Phlm'   : "Phm"  ,
	'Heb'    : "Heb"  ,
	'Jas'    : "Jam"  ,
	'1Pet'   : "1Pe"  ,
	'2Pet'   : "2Pe"  ,
	'1John'  : "1Jn"  ,
	'2John'  : "2Jn"  ,
	'3John'  : "3Jn"  ,
	'Jude'   : "Jud" ,
	'Rev'    : "Re"   ,
}

class SBLGNTParser(xml.sax.handler.ContentHandler):
    """Class to parse the SBL GNT XML file"""

    def __init__(self, parent):
        self.in_book = 0
        self.in_book_title = 0
        self.in_paragraph = 0
        self.in_verse = 0
        self.in_word = 0
        self.in_suffix = 0
        self.parent = parent

    def startElement(self, name, attrs):
        """Actions for encountering opening tags"""
        
        if name == "book":
	    # Open struct for book
            # Attribute is "id"
            self.in_book = 1

        # Looks like we don't have an equivalent for this in OpenScriptures
        #elif name == "title":
            #self.in_book_title = 1

        elif name == "verse-number":
            self.in_verse = 1
            # Close previous verse struct (if necessary) and open new verse struct
            # Attribute is "id"

        elif name == "p":
            # Open new paragraph struct
            self.in_paragraph = 1

        elif name == "w":
            self.in_word = 1

        elif name == "suffix":
            self.in_suffix = 1


    def characters(self, data):
        """Handle the tags which enclose data needed for import"""

        if self.in_word:
            # Here handle word tokens
            self.parent.add_token(data)

        elif self.in_suffix:
            # Here handle whitespace and punctuation tokens
            # TOOD: Fix this to split punctuation from whitespace            
            self.parent.add_token(data)

    def endElement(self, name):
        """Actions for encountering closing tags"""

        if name == "book":
	        # Close struct for book
            # Attribute is "id"
            self.in_book = 0

        # Looks like we don't have an equivalent for this in OpenScriptures
        #elif name == "title":
            #self.in_book_title = 0

        elif name == "verse-number":
            # Verse number tag is self-closing
            self.in_verse = 0

        elif name == "p":
            # Close current paragraph struct
            self.in_paragraph = 0

        elif name == "w":
            # Have already tokenized data, nothing more to do            
            self.in_word = 0

        elif name == "suffix":
            # Have already tokenized data, nothing more to do
            self.in_suffix = 0


# Below copied from Tischendorf importer


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

    def create_license(self):
        # TODO: Need to add SBLGNT license here
        pass

    def create_works(self):
        # Delete existing works
        delete_work(WORK1_ID)

        # Work for Kethiv edition (base text for qere)
        work1 = Work(
            id           = WORK1_ID,
            title        = "SBL Greek New Testament",
            language     = Language('grc'),
            type         = 'Bible',
            osis_slug    = 'SBLGNT',
            publish_date = datetime.date(2010, 10, 28),
            import_date  = datetime.datetime.now(),
            variant_bit  = WORK1_VARIANT_BIT,
            creator      = "Michael W. Holmes",
            source_url   = SOURCE_URL,
            license      = License.objects.get(url="http://www.sblgnt.com/license/")
        )
        work1.save()
        WorkServer.objects.create(
            work = work1,
            server = Server.objects.get(is_self = True)
        )

        
        return work1


    def handle(self, *args, **options):
        # Abort if MS has already been added (or --force not supplied)
        abort_if_imported(WORK1_ID, options["force"])

        # Download the source file
        download_resource(SOURCE_URL)

        # Create Works
        work1 = self.create_works()

        # Get the subset of OSIS book codes provided on command line
        limited_book_codes = []
        for arg in args:
            id_parts = arg.split(".")
            if id_parts[0] in osis.BOOK_ORDERS["Bible"]["KJV"]:
                limited_book_codes.append(id_parts[0])
        book_codes = osis.BOOK_ORDERS["Bible"]["KJV"]
        if len(limited_book_codes) > 0:
            book_codes = limited_book_codes

        # Read each of the Book files
        structCount = 1
        tokenCount = 1
        _zip = zipfile.ZipFile(os.path.basename(SOURCE_URL))
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
                source_url = "zip:" + SOURCE_URL + "!/Tischendorf-2.5/Unicode/" + BOOK_FILENAME_LOOKUP[book_code]
                #title = osis.BOOK_NAMES["Bible"][book_code]
            )

            structCount += 1
            bookTokens = []
            current_chapter = None
            current_verse = None
            lineNumber = -1

            for line in StringIO.StringIO(_zip.read("Tischendorf-2.5/Unicode/" + BOOK_FILENAME_LOOKUP[book_code])):
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
                if lineMatches.group('chapter') != current_chapter:
                    # End the previous chapter
                    close_structure(Structure.CHAPTER, bookTokens, structs)

                    # Start the next chapter
                    current_chapter = lineMatches.group('chapter')
                    structs[Structure.CHAPTER] = Structure(
                        work = work1, # remember work2 is subsumed by work1
                        type = Structure.CHAPTER,
                        position = structCount,
                        osis_id = book_code + "." + current_chapter,
                        numerical_start = current_chapter,
                        variant_bits = WORK2_VARIANT_BIT | WORK1_VARIANT_BIT
                    )
                    print(structs[Structure.CHAPTER].osis_id)
                    structCount += 1

                # New Verse start
                if lineMatches.group('verse') != current_verse:
                    # End the previous verse
                    close_structure(Structure.VERSE, bookTokens, structs)

                    # Start the next verse
                    current_verse = lineMatches.group('verse')
                    structs[Structure.VERSE] = Structure(
                        work = work1, # remember work2 is subsumed by work1
                        type = Structure.VERSE,
                        position = structCount,
                        osis_id = book_code + "." + current_chapter + "." + current_verse,
                        numerical_start = current_verse,
                        variant_bits = WORK2_VARIANT_BIT | WORK1_VARIANT_BIT
                    )
                    print(structs[Structure.VERSE].osis_id)
                    structCount += 1

                # End paragraph
                paragraph_marker = None
                if lineMatches.group('break') == 'P' and structs.has_key(Structure.PARAGRAPH):
                    assert(len(bookTokens) > 0)

                    paragraph_marker = Token(
                        data     = u"\u2029", #¶ "\n\n"
                        type     = Token.WHITESPACE, #i.e. PARAGRAPH
                        work     = work1,
                        position = tokenCount,
                        variant_bits = WORK2_VARIANT_BIT | WORK1_VARIANT_BIT
                    )
                    tokenCount += 1
                    paragraph_marker.save()
                    structs[Structure.PARAGRAPH].end_marker = paragraph_marker
                    close_structure(Structure.PARAGRAPH, bookTokens, structs)
                    bookTokens.append(paragraph_marker)

                # Start paragraph
                if len(bookTokens) == 0 or lineMatches.group('break') == 'P':
                    assert(not structs.has_key(Structure.PARAGRAPH))
                    print("¶")
                    structs[Structure.PARAGRAPH] = Structure(
                        work = work1, # remember work2 is subsumed by work1
                        type = Structure.PARAGRAPH,
                        position = structCount,
                        variant_bits = WORK2_VARIANT_BIT | WORK1_VARIANT_BIT
                    )
                    if paragraph_marker:
                        structs[Structure.PARAGRAPH].start_marker = paragraph_marker
                    structCount += 1

                # Insert whitespace
                if not paragraph_marker and len(bookTokens) > 0:
                    ws_token = Token(
                        data     = " ",
                        type     = Token.WHITESPACE,
                        work     = work1,
                        position = tokenCount,
                        variant_bits = WORK2_VARIANT_BIT | WORK1_VARIANT_BIT
                    )
                    tokenCount += 1
                    ws_token.save()
                    bookTokens.append(ws_token)

                assert(lineMatches.group('kethivPunc') == lineMatches.group('qerePunc'))
                assert(lineMatches.group('kethivStartBracket') == lineMatches.group('qereStartBracket'))
                assert(lineMatches.group('kethivEndBracket') == lineMatches.group('qereEndBracket'))

                #if string.find(line, '[') != -1 or string.find(line, ']') != -1 or lineMatches.group('kethiv') != lineMatches.group('qere'):
                #    print line
                #continue

                lineTokens = []

                # Open UNCERTAIN1 bracket
                assert(lineMatches.group('kethivStartBracket') == lineMatches.group('qereStartBracket'))
                if lineMatches.group('kethivStartBracket'):
                    assert(not structs.has_key(Structure.UNCERTAIN1))
                    print("### OPEN BRACKET")

                    # Make start_marker for UNCERTAIN1
                    open_bracket_token = Token(
                        data     = '[',
                        type     = Token.PUNCTUATION,
                        work     = work1,
                        position = tokenCount
                    )
                    tokenCount += 1
                    open_bracket_token.save()
                    lineTokens.append(open_bracket_token)

                    # Create the UNCERTAIN1 structure
                    structs[Structure.UNCERTAIN1] = Structure(
                        work = work1, # remember work2 is subsumed by work1
                        type = Structure.UNCERTAIN1,
                        position = structCount,
                        variant_bits = WORK2_VARIANT_BIT | WORK1_VARIANT_BIT,
                        start_marker = open_bracket_token
                    )
                    structCount += 1

                # Kethiv token
                token_work1 = Token(
                    data     = lineMatches.group('kethiv'),
                    type     = Token.WORD,
                    work     = work1,
                    position = tokenCount,
                    variant_bits = WORK1_VARIANT_BIT | WORK2_VARIANT_BIT,
                    relative_source_url = "#line(%d)" % lineNumber
                )
                if lineMatches.group('kethiv') == lineMatches.group('qere'):
                    token_work1.variant_bits = WORK1_VARIANT_BIT | WORK2_VARIANT_BIT
                else:
                    token_work1.variant_bits = WORK1_VARIANT_BIT
                tokenCount += 1
                token_work1.save()
                lineTokens.append(token_work1)

                # Make this token the start of the UNCERTAIN structure
                if lineMatches.group('kethivStartBracket'):
                    structs[Structure.UNCERTAIN1].start_token = token_work1

                # Qere token
                if lineMatches.group('kethiv') != lineMatches.group('qere'):
                    print("%s != %s" % (lineMatches.group('kethiv'), lineMatches.group('qere')))
                    token_work2 = Token(
                        data     = lineMatches.group('qere'),
                        type     = Token.WORD,
                        work     = work1, # yes, this should be work1
                        position = tokenCount,   #token_work1.position #should this be the same!?
                        variant_bits = WORK2_VARIANT_BIT,
                        relative_source_url = "#line(%d)" % lineNumber
                        # What will happen with range?? end_token = work1, but then work2?
                        # Having two tokens at the same position could mean that they are
                        #  co-variants at that one spot. But then we can't reliably get
                        #  tokens by a range? Also, the position can indicate transposition?
                    )
                    tokenCount += 1
                    token_work2.save()
                    lineTokens.append(token_work2)

                # Punctuation token
                assert(lineMatches.group('kethivPunc') == lineMatches.group('qerePunc'))
                if lineMatches.group('kethivPunc'):
                    punc_token = Token(
                        data     = lineMatches.group('kethivPunc'),
                        type     = Token.PUNCTUATION,
                        work     = work1,
                        position = tokenCount,
                        variant_bits = WORK1_VARIANT_BIT | WORK2_VARIANT_BIT
                    )
                    tokenCount += 1
                    punc_token.save()
                    lineTokens.append(punc_token)

                # Close UNCERTAIN1 bracket
                assert(lineMatches.group('kethivEndBracket') == lineMatches.group('qereEndBracket'))
                if lineMatches.group('kethivEndBracket'):
                    assert(structs.has_key(Structure.UNCERTAIN1))
                    print("### CLOSE BRACKET")

                    structs[Structure.UNCERTAIN1].end_token = lineTokens[-1]

                    # Make end_marker for UNCERTAIN1
                    close_bracket_token = Token(
                        data     = ']',
                        type     = Token.PUNCTUATION,
                        work     = work1,
                        position = tokenCount,
                        variant_bits = WORK1_VARIANT_BIT | WORK2_VARIANT_BIT
                    )
                    tokenCount += 1
                    close_bracket_token.save()

                    # Close the UNCERTAIN1 structure
                    structs[Structure.UNCERTAIN1].end_marker = close_bracket_token
                    close_structure(Structure.UNCERTAIN1, bookTokens, structs)
                    lineTokens.append(open_bracket_token)

                # Set the start_token for each structure that isn't set
                for struct in structs.values():
                    if struct.start_token is None:
                        struct.start_token = lineTokens[0]

                for token in lineTokens:
                    bookTokens.append(token)

            for structType in structs.keys():
                close_structure(structType, bookTokens, structs)

        print("structCount: %s" % str(structCount))
        print("tokenCount:  %s" % str(tokenCount))

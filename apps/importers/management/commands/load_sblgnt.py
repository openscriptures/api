# encoding: utf-8
#
# OpenScriptures importer for the SBL Greek New Testament Tex
# http://www.sblgnt.com/

# Standard library imports
import datetime
from optparse import make_option
import os
import unicodedata
import xml.sax
import zipfile
import StringIO

# Django imports
from django.core.management.base import BaseCommand

# Open Scriptures imports
from apps.core import osis
from apps.importers.import_helpers import OpenScripturesImport
from apps.texts.models import Work, Token, Structure, WorkServer
from apps.core.models import Language, License, Server

# TODO: Some of this might be better defined as SETTING
SOURCE_URL = "http://sblgnt.com/download/SBLGNTxml.zip"

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

    def __init__(self, importer):
        self.in_text = 0
        self.in_book = 0
        self.in_book_title = 0
        self.in_paragraph = 0
        self.in_verse = 0
        self.in_word = 0
        self.in_suffix = 0
        self.children_in_p = -1
        self.importer = importer

    def startElement(self, name, attrs):
        """Actions for encountering opening tags"""
        
        if name == "book":
            # Once we are in the book tag, the real text has begun
            self.in_text = 1            
            self.in_book = 1
            # Reset chapter and verses
            self.current_verse = 0
            self.current_chapter = 0
            (name, value) = attrs.items()[0]
            for key in BOOK_ID_LOOKUP:
                if BOOK_ID_LOOKUP[key] == value:
                    self.importer.current_book = key
            self.importer.create_book_struct()

        elif name == "verse-number":
            self.in_verse = 1
            # Close previous verse struct (if necessary)
            self.importer.close_structure("verse")
            
        elif name == "p":
            # Open new paragraph struct
            self.in_paragraph = 1
            # Detect if this is a self-closing tag            
            self.children_in_p = -1
            # Avoid pre-text <p> tags            
            if self.in_text:
                self.importer.create_paragraph()

        elif name == "w":
            self.in_word = 1

        elif name == "suffix":
            self.in_suffix = 1

        if self.in_paragraph:
            self.children_in_p +=1

    def characters(self, data):
        """Handle the tags which enclose data needed for import"""

        if self.in_word:
            # Here handle word tokens
            self.importer.create_token(data)
            # Link structures to newly-created start_tokens
            # Needs to come after token creation is done, but not sure this is the best spot
            self.importer.link_start_tokens()

        elif self.in_suffix:
            # Here handle whitespace and punctuation tokens
            # TOOD: Fix this to split punctuation from whitespace            
            suffix = data.split(" ")
            # Test to see if he suffix contains punctuation.
            # Will return false if the split resulted in a null value in array position [0]            
            if suffix[0]:
                self.importer.create_punct_token(suffix[0])
            self.importer.create_whitespace_token()

        elif self.in_verse:
            # Handle new verse structs and chapter structs
            # Inclusion of colon means a new chapter
            if ":" in data:              
                chapter_verse = data.split(":")                
                self.importer.close_structure("chapter")
                self.importer.current_chapter = chapter_verse[0]
                self.importer.create_chapter_struct() 
                self.importer.current_verse = chapter_verse[1]                  
            else:
                self.importer.current_verse = data
            self.importer.create_verse_struct()

    def endElement(self, name):
        """Actions for encountering closing tags"""

        if name == "book":
	        # Close struct for book
            # Attribute is "id"
            self.in_book = 0
            #self.importer.close_structure(Structure.BOOK)
            self.importer.link_start_tokens()            
            for structElement in self.importer.structs.keys():               
                self.importer.close_structure(structElement)
            # Re-initialize the bookTokens array 
            self.importer.bookTokens = []

        elif name == "verse-number":
            # Verse number tag is self-closing
            self.in_verse = 0

        elif name == "p":
            # If this is a self-closing tag, link start-token to paragraph token
            self.in_paragraph = 0
            if self.children_in_p == 0 and self.in_text:
                print "<p />"
                self.importer.link_start_tokens()

        elif name == "w":
            # Have already tokenized data, nothing more to do            
            self.in_word = 0

        elif name == "suffix":
            # Have already tokenized data, nothing more to do
            self.in_suffix = 0

class Command(BaseCommand):
    # Not implementing selecting books right now
    #args = '<Jude John ...>'
    #help = 'Limits the scope of the load to just to the books specified.'

    option_list = BaseCommand.option_list + (
        make_option('--force',
            action='store_true',
            dest='force',
            default=False,
            help='Force load despite it already being loaded'),
        )


### Main command handle below

    def handle(self, *args, **options):
        self.importer = OpenScripturesImport()

        # Abort if MS has already been added (or --force not supplied)
        self.importer.abort_if_imported("SBLGNT", options["force"])

        # Download the source file
        self.importer.download_resource(SOURCE_URL)

		# Create license
        if len(License.objects.filter(url="http://www.sblgnt.com/license/")) == 0:
            License.objects.create(
                name        = "SBLGNT License",
                abbreviation    = "SBLGNT",
                url             = "http://www.sblgnt.com/license/",
            )

        # Create Works
        if len(Work.objects.filter(osis_slug="SBLGNT")) > 0:        
            self.importer.delete_work(Work.objects.get(osis_slug="SBLGNT"))
        self.importer.work1 = Work(
            #id           = WORK1_ID,
            title        = "SBL Greek New Testament",
            language     = Language('grc'),
            type         = 'Bible',
            osis_slug    = 'SBLGNT',
            publisher    = 'Logos',
            publish_date = datetime.date(2010, 10, 28),
            import_date  = datetime.datetime.now(),
            creator      = "Michael W. Holmes",
            source_url   = SOURCE_URL,
            license      = License.objects.get(url="http://www.sblgnt.com/license/")
        )
        self.importer.work1.save()
        
        WorkServer.objects.create(
            work = self.importer.work1,
            server = Server.objects.get(is_self = True)
        )

        # Get the subset of OSIS book codes provided on command line
        #limited_book_codes = []
        #for arg in args:
            #id_parts = arg.split(".")
            #if id_parts[0] in osis.BOOK_ORDERS["Bible"]["KJV"]:
                #limited_book_codes.append(id_parts[0])
        #book_codes = osis.BOOK_ORDERS["Bible"]["KJV"]
        #if len(limited_book_codes) > 0:
            #book_codes = limited_book_codes
        #self.importer.book_codes = book_codes
        self.importer.book_codes = osis.BOOK_ORDERS["Bible"]["KJV"]

		# Initialize the parser and set it up
        self.parser = xml.sax.make_parser()        
        self.parser.setContentHandler(SBLGNTParser(self.importer))
        _zip = zipfile.ZipFile(os.path.basename(SOURCE_URL))
        self.parser.parse(StringIO.StringIO(_zip.read("sblgnt.xml")))
        print "Total tokens %d" % self.importer.tokenCount
        print "Total structures: %d" % self.importer.structCount


# TODO
# Handle limited books
# Titles

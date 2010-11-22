# encoding: utf-8
#
# OpenScriptures importer for the Crosswire KJV 2006 text
# http://www.crosswire.org/~dmsmith/kjv2006/index.html
# Going to use the KJV lite XML for now, but will eventually support the
# full text in order to get all the free metadata.

# Standard library imports
import datetime
from optparse import make_option
import os
import re
import unicodedata
import xml.sax
import zipfile
import StringIO

# Django imports
from django.core.management.base import BaseCommand

# Open Scriptures imports
from apps.core import osis
from apps.importers.management.openscripturesimport import OpenScripturesImport
from apps.texts.models import Work, Token, Structure, WorkServer
from apps.core.models import Language, License, Server

# TODO: Some of this might be better defined as SETTING
SOURCE_URL = "http://www.crosswire.org/~dmsmith/kjv2006/sword/kjvxml.zip"

PUNC_CHRS = re.escape(ur'.·,;:!?"\'')

class KJVParser(xml.sax.handler.ContentHandler):
    """Class to parse the SBL GNT XML file"""

    def __init__(self, importer):
        self.in_text = 0
        self.in_book = 0
        self.in_title = 0
        self.in_chapter = 0
        self.in_verse = 0
        self.in_transChange = 0
        self.in_note = 0
        self.in_milestone = 0
        self.importer = importer

    def startElement(self, name, attrs):
        """Actions for encountering opening tags"""
        
        if name == "div":
            # Once we are in the book tag, the real text has begun
            self.in_text = 1            
            self.in_book = 1
            # Reset chapter and verses
            self.current_verse = 0
            self.current_chapter = 0
            (name, value) = attrs.items()[2]
            self.importer.current_book = value
            self.importer.create_book_struct()

        elif name == "chapter":
            self.in_chapter = 1
            # Get the chapter number from the OSIS id
            (name, value) = attrs.items()[1]
            self.importer.current_chapter =  value.split(".")[1]
            self.importer.create_chapter_struct()
            
        elif name == "title":
            self.in_title = 1
            # Avoid pre-text title tags
            if self.in_text:
                print "Title"
                self.importer.create_title_struct()
 
        elif name == "verse":
            names = []
            values = []
            # Get the verse number from the OSIS id
            for each in attrs.items():
                (name, value) = each
                names.append(name)
                values.append(value)
            if "sID" in names:
                self.importer.current_verse = values[0].split(".")[2]
                self.importer.create_verse_struct()
                self.in_verse = 1
            else:
                # Add a space at the end of eeach verse, because they are missing.
                self.importer.create_whitespace_token()
                self.importer.close_structure(Structure.VERSE)
                self.in_verse = 0
            
        elif name == "transChange":
            self.in_transChange = 1
            
        elif name == "note":
            self.in_note = 1
            
        elif name == "milestone":
            self.in_miltestone = 1
            if self.in_text:
                self.importer.create_paragraph()

    def characters(self, data):
        """Handle the tags which enclose data needed for import"""
        # Only import inside of verses, avoiding new lines
        if self.in_text and (self.in_title or self.in_verse) and (not self.in_note):
            # REGEX to the rescue!
            # Clump alphanumeric characters, including the apostraphe
            punct = re.compile("[%s]" % PUNC_CHRS)
            punct_space = re.compile("[%s]\s" % PUNC_CHRS)
            tokens = re.split('(\W+)', data)
            # Last item is null
            for i in range(len(tokens)):
                if tokens[i] == ' ':
                    self.importer.create_whitespace_token()
                
                # Match the first character for punctuation
                elif punct_space.match(tokens[i]):
                    self.importer.create_punct_token(tokens[i].split(" ")[0])
                    self.importer.create_whitespace_token()
                # Fairly sure all punctuation tokens are followed by spaces
                # But just to be safe
                #elif punct.match(tokens[i]):
                    #self.importer.create_punct_token(tokens[i])
                    
                # Ensure we aren't adding blank tokens
                elif tokens[i] != '':
                    self.importer.create_token(tokens[i])
                
                # Link structures to newly-created start_tokens
                # Needs to come after first token is created
                if i == 0:
                    self.importer.link_start_tokens()

    def endElement(self, name):
        """Actions for encountering closing tags"""

        if name == "div":
            self.in_book = 0
            self.importer.link_start_tokens()            
            for structType in self.importer.structs.keys():               
                self.importer.close_structure(structType)
            # Re-initialize the bookTokens array 
            self.importer.bookTokens = []

        elif name == "chapter":
            self.in_chapter = 0
            self.importer.close_structure(Structure.CHAPTER)

        elif name == "title":
            self.in_title = 0
            if self.in_text:
                self.importer.close_structure(Structure.TITLE)
            
        elif name == "transChange":
            self.in_transChange = 0
            
        elif name == "note":
            self.in_note = 0
            
        elif name == "milestone":
            self.in_milestone = 0

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


### Main command handle below

    def handle(self, *args, **options):
        self.importer = OpenScripturesImport()

        # Abort if MS has already been added (or --force not supplied)
        self.importer.abort_if_imported("KJV", options["force"])

        # Download the source file
        self.importer.download_resource(SOURCE_URL)

        # Create Works
        if len(Work.objects.filter(osis_slug="KJV")) > 0:        
            self.importer.delete_work(Work.objects.get(osis_slug="KJV"))
        self.importer.work1 = Work(
            #id           = WORK1_ID,
            title        = "King James Version (1769)",
            language     = Language('eng'),
            type         = 'Bible',
            osis_slug    = 'KJV',
            publisher    = 'Crosswire',
            publish_date = datetime.date(2006, 01, 01),
            import_date  = datetime.datetime.now(),
            #creator      = "Michael W. Holmes",
            source_url   = SOURCE_URL,
            license      = License.objects.get(url="http://creativecommons.org/licenses/publicdomain/")
        )
        self.importer.work1.save()
        
        WorkServer.objects.create(
            work = self.importer.work1,
            server = Server.objects.get(is_self = True)
        )

        # Get the subset of OSIS book codes provided on command line
        limited_book_codes = []
        for arg in args:
            id_parts = arg.split(".")
            if id_parts[0] in osis.BOOK_ORDERS["Bible"]["KJV"]:
                limited_book_codes.append(id_parts[0])
        book_codes = osis.BOOK_ORDERS["Bible"]["KJV"]
        if len(limited_book_codes) > 0:
            book_codes = limited_book_codes
        self.importer.book_codes = book_codes

		# Initialize the parser and set it up
        self.parser = xml.sax.make_parser()        
        self.parser.setContentHandler(KJVParser(self.importer))
        _zip = zipfile.ZipFile(os.path.basename(SOURCE_URL))
        self.parser.parse(StringIO.StringIO(_zip.read("kjvlite.xml")))
        print "Total tokens %d" % self.importer.tokenCount
        print "Total structures: %d" % self.importer.structCount


# TODO
# Handle limited books

#!/usr/bin/env python
# encoding: utf-8

import datetime
import os
import re
import StringIO
import unicodedata
import zipfile

from optparse import make_option

from django.core.management.base import BaseCommand

from openscriptures_api import osis
from openscriptures_api_texts.management.import_helpers import abort_if_imported
from openscriptures_api_texts.management.import_helpers import close_structure
from openscriptures_api_texts.management.import_helpers import delete_work
from openscriptures_api_texts.management.import_helpers import download_resource
from openscriptures_api_texts.models import Work, Token, Structure, WorkServer
from openscriptures_api.models import Language, License, Server

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
    
    def handle(self, *args, **options):
        # Abort if MS has already been added (or --force not supplied)
        #TODO figure out importance of "WORK1_ID" to this function
        abort_if_imported(WORK1_ID, options["force"])

        # Download the source file

### ORIGINAL FILE BELOW ###



# First step is to fetch the data from the server via script by Tom Brazier which converts the source from Betacode to Unicode and the Unbound Bible file format
# TODO Change this to a class or function instead of executing external script
if(not os.path.exists('greek_byzantine_2005_parsed_punc_utf8.txt')):
    execfile('greek_byzantine_2005_parsed.prepare_data.py')

import_helpers.delete_work(msID)
msWork = Work(
    id           = msID,
    title        = "Byzantine/Majority Text (2005)",
    description  = "Parsed with punctuation, accents and breathings",
    abbreviation = 'Byz-2005',
    language     = Language('grc'),
    type         = 'Bible',
    osis_slug    = 'Byzantine',
    publish_date = date(2005, 1, 1),
    originality  = 'manuscript-edition',
    creator      = "Maurice A. Robinson and William G. Pierpont.",
    url          = "http://www.byztxt.com/download/BYZ05CCT.ZIP",
    license      = License.objects.get(url="http://creativecommons.org/licenses/publicdomain/")
)
msWork.save()

# The followig regular epression identifies the parts of the following line:
#40N	1	1		10	Βίβλος G976 N-NSF γενέσεως G1078 N-GSF Ἰησοῦ G2424 N-GSM χριστοῦ G5547 N-GSM , υἱοῦ G5207 N-GSM Δαυίδ G1138 N-PRI , υἱοῦ G5207 N-GSM Ἀβραάμ G11 N-PRI .
lineParser = re.compile(ur"""^
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
tokenParser = re.compile(ur"""
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

bookRefs = []
chapterRefs = []
verseRefs = []
tokens = []
previousTokens = []
tokenPosition = 0

f = open('greek_byzantine_2005_parsed_punc_utf8.txt', 'r')
for verseLine in f:
    if(verseLine.startswith('#')):
        continue
    verseLine = unicodedata.normalize("NFC", unicode(verseLine, 'utf-8'))
    verseInfo = lineParser.match(verseLine)
    if(not verseInfo):
        raise Exception("Parse error on line: " + verseLine)
    if(not verseInfo.group('data') or UNBOUND_CODE_TO_OSIS_CODE[verseInfo.group('book')] not in OSIS_BIBLE_BOOK_CODES):
        continue
    meta = verseInfo.groupdict()

    # Create book ref if it doesn't exist
    if(not len(bookRefs) or bookRefs[-1].osis_id != UNBOUND_CODE_TO_OSIS_CODE[meta['book']]):
        print UNBOUND_CODE_TO_OSIS_CODE[meta['book']]
        
        # Reset tokens
        previousTokens = tokens
        tokens = []
        
        # Close book and chapter refs
        if(len(previousTokens)):
            bookRefs[-1].end_token = previousTokens[-1]
            bookRefs[-1].save()
            chapterRefs[-1].end_token = previousTokens[-1]
            chapterRefs[-1].save()
        chapterRefs = []
        verseRefs = []
        
        # Set up the book ref
        bookRef = Ref(
            work = msWork,
            type = Ref.BOOK,
            osis_id = UNBOUND_CODE_TO_OSIS_CODE[meta['book']],
            position = len(bookRefs),
            title = OSIS_BOOK_NAMES[UNBOUND_CODE_TO_OSIS_CODE[meta['book']]]
        )
        #bookRef.save()
        #bookRefs.append(bookRef)
        
    # So here we need to have tokenParser match the entire line
    pos = 0
    verseTokens = []
    while(pos < len(meta['data'])):
        tokenMatch = tokenParser.match(meta['data'], pos)
        if(not tokenMatch):
            print "%s %02d %02d" % (meta['book'], int(meta['chapter']), int(meta['verse']))
            print "Unable to parse at position " + str(pos) + ": " + meta['data']
            raise Exception("Unable to parse at position " + str(pos) + ": " + meta['data'])
        
        # Insert token
        token = Token(
            data     = tokenMatch.group('word'),
            type     = Token.WORD,
            work     = msWork,
            position = tokenPosition
        )
        tokenPosition = tokenPosition + 1
        token.save()
        tokens.append(token)
        verseTokens.append(token)
        
        # Insert punctuation
        if(tokenMatch.group('punctuation')):
            token = Token(
                data     = tokenMatch.group('punctuation'),
                type     = Token.PUNCTUATION,
                work     = msWork,
                position = tokenPosition
            )
            tokenPosition = tokenPosition + 1
            token.save()
            tokens.append(token)
            verseTokens.append(token)
        
        # Token Parsing
        #strongs = [tokenMatch.group('strongs1')]
        #if(tokenMatch.group('strongs2')):
        #    strongs.append(tokenMatch.group('strongs2'))
        parsing = TokenParsing(
            token = token,
            raw = tokenMatch.group("rawParsing"),
            #parse = tokenMatch.group('parsing'),
            #strongs = ";".join(strongs),
            language = Language('grc'),
            work = msWork
        )
        parsing.save()
        
        # Make this token the first in the book ref, and set the first token in the book
        if len(tokens) == 1:
            bookRef.start_token = tokens[0]
            bookRef.save()
            bookRefs.append(bookRef)
        
        # Set up the Chapter ref
        if(not len(chapterRefs) or chapterRefs[-1].numerical_start != meta['chapter']):
            if(len(chapterRefs)):
                chapterRefs[-1].end_token = tokens[-2]
                chapterRefs[-1].save()
            chapterRef = Ref(
                work = msWork,
                type = Ref.CHAPTER,
                osis_id = ("%s.%s" % (bookRefs[-1].osis_id, meta['chapter'])),
                position = len(chapterRefs),
                parent = bookRefs[-1],
                numerical_start = meta['chapter'],
                start_token = tokens[-1]
            )
            chapterRef.save()
            chapterRefs.append(chapterRef)
        
        pos = tokenMatch.end()
        
    # Create verse ref
    verseRef = Ref(
        work = msWork,
        type = Ref.VERSE,
        osis_id = ("%s.%s.%s" % (bookRefs[-1].osis_id, meta['chapter'], meta['verse'])),
        position = len(verseRefs),
        parent = chapterRefs[-1],
        numerical_start = meta['verse'],
        start_token = verseTokens[0],
        end_token = verseTokens[-1]
    )
    verseRef.save()
    verseRefs.append(verseRef)

#Save all books, chapters
bookRefs[-1].end_token = tokens[-1]
bookRefs[-1].save()
chapterRefs[-1].end_token = tokens[-1]
for chapterRef in chapterRefs:
    chapterRef.save()


f.close()

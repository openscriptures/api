#!/usr/bin/env python
# encoding: utf-8

work1_id = 1 # Tischendorf Kethiv
work1_variant_bit = 0b00000001
work2_id = 2 # Tischendorf Qere
work2_variant_bit = 0b00000010

import sys, string, os, re, unicodedata, urllib, zipfile, StringIO
from datetime import date
from django.core.management import setup_environ
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../../')) #There's probably a better way of doing this
from openscriptures import settings
setup_environ(settings)
from openscriptures.api.models import *
from openscriptures.api.importers import import_helpers

# Abort if MS has already been added (or --force not supplied)
import_helpers.abort_if_imported(work1_id)

# Download the source file
source_url = "http://files.morphgnt.org/tischendorf/Tischendorf-2.5.zip"
import_helpers.download_resource(source_url)

# Delete existing works
import_helpers.delete_work(work2_id)
import_helpers.delete_work(work1_id)

# Work for Kethiv edition (base text for qere)
work1 = Work(
    id           = work1_id,
    title        = "Tischendorf 8th ed. v2.5 (Kethiv)",
    language     = Language('grc'),
    type         = 'Bible',
    osis_slug    = 'Tischendorf',
    publish_date = date(2009, 1, 1),
    variant_bit  = work1_variant_bit,
    creator      = "<a href='http://en.wikipedia.org/wiki/Constantin_von_Tischendorf' title='Constantin von Tischendorf @ Wikipedia'>Constantin von Tischendorf</a>. Based on G. Clint Yale's Tischendorf text and on Dr. Maurice A. Robinson's Public Domain Westcott-Hort text. Edited by <a href='http://www.hum.aau.dk/~ulrikp/'>Ulrik Sandborg-Petersen</a>.",
    source_url   = source_url,
    license      = License.objects.get(url="http://creativecommons.org/licenses/publicdomain/")
)
work1.save()


# Work for Qere edition (Kethiv is base text)
import_helpers.delete_work(work2_id)
work2 = Work(
    id           = work1_id,
    title        = "Tischendorf 8th ed. v2.5 (Qere)",
    language     = Language('grc'),
    type         = 'Bible',
    osis_slug    = 'Tischendorf',
    publish_date = date(2009, 1, 1),
    variant_bit  = work2_variant_bit,
    variants_for_work = work1,
    creator      = "<a href='http://en.wikipedia.org/wiki/Constantin_von_Tischendorf' title='Constantin von Tischendorf @ Wikipedia'>Constantin von Tischendorf</a>. Based on G. Clint Yale's Tischendorf text and on Dr. Maurice A. Robinson's Public Domain Westcott-Hort text. Edited by <a href='http://www.hum.aau.dk/~ulrikp/'>Ulrik Sandborg-Petersen</a>.",
    source_url   = source_url,
    license      = License.objects.get(url="http://creativecommons.org/licenses/publicdomain/")
)
work2.save()




bookFilenameLookup = {
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

#NOTICE: We need to do the same thing with Tischendorf that we did with TNT: there is a corrected edition
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


#puncchrs = re.escape(''.join(unichr(x) for x in range(65536) if unicodedata.category(unichr(x)) == 'Po'))
puncchrs = re.escape(ur'.·,;:!?"\'')
lineParser = re.compile(ur"""^
        (?P<book>\S+)\s+            # Book (corresponds to the filename, which is the Online Bible standard)
        (?P<chapter>\d+):           # Chapter
        (?P<verse>\d+)\.            # Verse
        (?P<position>\d+)\s+        # word-within-verse
        (?P<break>\S)\s+            # Pagraph break ("P") / Chapter break ("C") / No break (".")
        (?P<kethivStartBracket>\[)?
        (?P<kethiv>\S+?)            # The text as it is written in the printed Tischendorf (Kethiv)
        (?P<kethivPunc>[%s])?\s+    # Kethiv punctuation
        (?P<kethivEndBracket>\])?
    (?P<rawParsing>
        (?P<qereStartBracket>\[)?
        (?P<qere>\S+?)              # The text as the editor thinks it should have been (Qere)
        (?P<qerePunc>  [%s])?\s+    # Qere punctuation
        (?P<qereEndBracket>\])?
        (?P<morph>\S+)\s+           # The morphological tag (following the Qere)
        (?P<strongsNumber>\d+)\s+   # The Strong's number (following the Qere)
        (?P<strongsLemma>.+?)       # Lemma which corresponds to The NEW Strong's Complete Dictionary of Bible Words. (There may be several words in each lemma.)
        \s+!\s+                     # A " ! " separates the lemmas
        (?P<anlexLemma>.+?)         # Lemma which corresponds to Friberg, Friberg and Miller's ANLEX. (There may be several words in each lemma.)
    )
    \s*$""" % (puncchrs, puncchrs),
    re.VERBOSE
)

#works = [work1, work2]
#bookRefs = []
#bookTokens = [[], []]
#openBrackets = [0,0]
#precedingTokenCount = 0

structCount = 0
tokenCount = 0

zip = zipfile.ZipFile(os.path.basename(source_url))
for book_code in OSIS_BIBLE_BOOK_CODES:
    #TEMP:
    if book_code != "Eph" and book_code != "2Cor":
        continue
    
    if not bookFilenameLookup.has_key(book_code):
        continue
    
    print OSIS_BOOK_NAMES[book_code]
    
    # Set up the book ref
    structs = {}
    structs[TokenStructure.BOOK] = TokenStructure(
        work = work1,
        type = TokenStructure.BOOK,
        osis_id = book_code,
        position = structCount,
        variant_bits = work2_variant_bit | work1_variant_bit
        #title = OSIS_BOOK_NAMES[book_code]
    )
    structCount += 1
    
    tokens = {}
    tokens[TokenStructure.BOOK] = []
    tokens[TokenStructure.CHAPTER] = []
    tokens[TokenStructure.VERSE] = []
    tokens[TokenStructure.PARAGRAPH] = []
    tokens[TokenStructure.UNCERTAIN1] = []
    
    for line in StringIO.StringIO(zip.read("Tischendorf-2.5/Unicode/" + bookFilenameLookup[book_code])):
        lineMatches = lineParser.match(unicodedata.normalize("NFC", unicode(line, 'utf-8')))
        if lineMatches is None:
            print " -- Warning: Unable to parse line: " + line 
            continue
        
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
            assert(not structs.has_key(TokenStructure.UNCERTAIN1))
            
            # Make start_marker_token for UNCERTAIN1
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
            structs[TokenStructure.UNCERTAIN1] = TokenStructure(
                work = work1, # remember work2 is subsumed by work1
                type = TokenStructure.UNCERTAIN1,
                position = structCount,
                variant_bits = work2_variant_bit | work1_variant_bit,
                start_marker_token = open_bracket_token
            )
            structCount += 1
        
        # Kethiv token
        token_work1 = Token(
            data     = lineMatches.group('kethiv'),
            type     = Token.WORD,
            work     = work1,
            position = tokenCount,
            variant_bits = work1_variant_bit | work2_variant_bit
        )
        if lineMatches.group('kethiv') == lineMatches.group('qere'):
            token_work1.variant_bits = work1_variant_bit | work2_variant_bit
        else:
            token_work1.variant_bits = work1_variant_bit
        tokenCount += 1
        token_work1.save()
        lineTokens.append(token_work1)
        
        # Make this token the start of the UNCERTAIN structure
        if lineMatches.group('kethivStartBracket'):
            structs[TokenStructure.UNCERTAIN1].start_token = token_work1
        
        # Qere token
        if lineMatches.group('kethiv') != lineMatches.group('qere'):
            token_work2 = Token(
                data     = lineMatches.group('qere'),
                type     = Token.WORD,
                work     = work1, # yes, this should be work1
                position = tokenCount,   #token_work1.position #should this be the same!?
                variant_bits = work2_variant_bit
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
                variant_bits = work1_variant_bit | work2_variant_bit
            )
            tokenCount += 1
            punc_token.save()
            lineTokens.append(punc_token)
            
            pass
        
        # Close UNCERTAIN1 bracket
        assert(lineMatches.group('kethivEndBracket') == lineMatches.group('qereEndBracket'))
        if lineMatches.group('kethivEndBracket'):
            assert(structs.has_key(TokenStructure.UNCERTAIN1))
            
            structs[TokenStructure.UNCERTAIN1].end_token = lineTokens[-1]
            
            # Make end_marker_token for UNCERTAIN1
            close_bracket_token = Token(
                data     = ']',
                type     = Token.PUNCTUATION,
                work     = work1,
                position = tokenCount,
                variant_bits = work1_variant_bit | work2_variant_bit
            )
            tokenCount += 1
            lineTokens.append(open_bracket_token)
            
            # Close the UNCERTAIN1 structure
            structs[TokenStructure.UNCERTAIN1].end_marker_token = close_bracket_token
            structs[TokenStructure.UNCERTAIN1].save()
            del structs[TokenStructure.UNCERTAIN1]
        
        
        #TODO: Here, create a token for startBracket, kethivWord, qereWord, punc, and endBracket
        #      and iterate over them. A structure will need to be created for the brackets
        
        for token in lineTokens:
            
            pass
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        continue
        
        
        
        # CHAPTER (TODO: Is this even needed?)
        if line.group('break') == 'C':
            # Close the previously opened chapter
            if structs.has_key(TokenStructure.CHAPTER) and len(tokens[TokenStructure.BOOK]) != 0:
                structs[TokenStructure.CHAPTER].end_token = tokens[TokenStructure.BOOK][-1]
                structs[TokenStructure.CHAPTER].save()
            
            # Reset chapter tokens
            tokens[TokenStructure.CHAPTER] = []
            
            # Create new chapter
            structs[TokenStructure.CHAPTER] = TokenStructure(
                work = work1, # remember work2 is subsumed by work1
                type = TokenStructure.CHAPTER,
                osis_id = book_code + '.' + line.group('chapter'),
                position = structCount,
                variant_bits = work2_variant_bit | work1_variant_bit,
                #start_token = ???
            )
            structCount += 1
            
        
        
        # Token first?
        #if word.group('break') == 'P' or len(tokens[TokenStructure.BOOK]) == 0:
        
        continue
        
        
        
        if word.group('break') == 'P' or len(tokens[TokenStructure.BOOK]) == 0:
            print line
            
            # Note: This token need not always be created!
            if word.group('break') == 'P':
                token = Token(
                    data     = "\n\n", #¶
                    type     = Token.PUNCTUATION,
                    work     = work1,
                    position = tokenCount,
                    variant_bits = work2_variant_bit | work1_variant_bit
                )
                tokenCount += 1
                token.save()
            
                # Set paragraph end marker
                if structs.has_key(TokenStructure.PARAGRAPH):
                    structs[TokenStructure.PARAGRAPH].end_marker_token = token
                    structs[TokenStructure.PARAGRAPH].save()
            
            
            # Create new paragraph structure
            structs[TokenStructure.PARAGRAPH] = TokenStructure(
                work = work1,
                type = TokenStructure.PARAGRAPH,
                osis_id = book_code,
                position = structCount,
                variant_bits = work2_variant_bit | work1_variant_bit,
                start_marker_token = token
            )
            structs[TokenStructure.PARAGRAPH].save()
            structCount += 1
            
            
            #del tokens[TokenStructure.BOOK]
            #tokens.clear()
        
        if token is not None:
            tokens[TokenStructure.BOOK].append(token)
        
        
        
        
        #if string.find(line, '[') != -1 or string.find(line, ']') != -1 or word.group('kethiv') != word.group('qere'):
        #    print line
        continue
        
        
        #if word.group('kethiv') != word.group('qere'):
        #    print line #print word.group('kethiv') + " -- " + word.group('qere')
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    continue
    
    #precedingTokenCount = precedingTokenCount + len(max(bookTokens[0], bookTokens[1]))

    
    for line in StringIO.StringIO(zip.read("Tischendorf-2.5/Unicode/" + bookFilenameLookup[book_code])):
        line = unicodedata.normalize("NFC", unicode(line, 'utf-8'))
        
        word = lineParser.match(line)
        if word is None:
            print " -- Warning: Unable to parse line: " + line 
            continue
        
        # If this is a paragraph break, insert new paragraph token
        if word.group('break') == 'P':
            token = Token(
                data     = "¶",
                type     = Token.PUNCTUATION,
                work     = work1,
                position = precedingTokenCount + len(bookTokens),
                variant_bits = work2_variant_bit | work1_variant_bit
            )
            token.save()
            bookTokens.append(token) #NOTE: identical for both Qere and Kethiv, so no variant group needed
        
        # Insert whitespace if preceding token isn't a puctuation or whitespace
        elif word.group('break') == '.' and len(bookTokens) and bookTokens[-1].type not in (Token.PUNCTUATION, Token.WHITESPACE):
            token = Token(
                data     = " ",
                type     = Token.WHITESPACE,
                work     = work2,
                position = precedingTokenCount + len(bookTokens),
                variant_bits = work2_variant_bit | work1_variant_bit
            )
            token.save()
            bookTokens.append(token) #NOTE: identical for both Qere and Kethiv, so no variant group needed
        
        if word.group('qereStartBracket'):
            openBrackets[0] += 1
        if word.group('kethivStartBracket'):
            openBrackets[1] += 1
        
        # Insert token
        #QUESTION: If the token is identical for both kethiv and qere, what if
        #          don't provide variants? Is it even necessary? Will we even be
        #          able to query tokens that don't have a variant?
        token = Token(
            data     = word.group('qere'),
            type     = Token.WORD,
            work     = work2,
            position = precedingTokenCount + len(bookTokens)
        )
        token.save()
        bookTokens.append(token)
        
        # Token Parsing
        parsing = TokenParsing(
            token = token,
            parse = word.group('morph'),
            strongs = word.group('strongsNumber'),
            lemma = word.group('strongsLemma') + '; ' + word.group('anlexLemma'),
            language = Language('grc'),
            work = work2
        )
        parsing.save()
        
        # Insert punctuation
        if(word.group('qerePunc')):
            token = Token(
                data     = word.group('qerePunc'),
                type     = Token.PUNCTUATION,
                work     = work2,
                position = precedingTokenCount + len(bookTokens)
            )
            token.save()
            bookTokens.append(token)

        if word.group('qereEndBracket'):
            openBrackets[0] -= 1
        if word.group('kethivEndBracket'):
            openBrackets[1] -= 1

        # Make this token the first in the book ref, and set the first token in the book
        if len(bookTokens) == 1:
            bookRef.start_token = bookTokens[0]
            bookRef.save()
            bookRefs.append(bookRef)
        
        # Set up the Chapter ref
        if(not len(chapterRefs) or word.group('chapter') != chapterRefs[-1].numerical_start):
            if(len(chapterRefs)):
                chapterRefs[-1].end_token = bookTokens[-2]
            chapterRef = Ref(
                work = work2,
                type = Ref.CHAPTER,
                osis_id = ("%s.%s" % (book_code, word.group('chapter'))),
                position = len(chapterRefs),
                parent = bookRef,
                numerical_start = word.group('chapter'),
                start_token = bookTokens[-1]
            )
            chapterRef.save()
            chapterRefs.append(chapterRef)
        
        # Set up the Verse Ref
        if(not len(verseRefs) or word.group('verse') != verseRefs[-1].numerical_start):
            if(len(verseRefs)):
                verseRefs[-1].end_token = bookTokens[-2]
            verseRef = Ref(
                work = work2,
                type = Ref.VERSE,
                osis_id = ("%s.%s" % (chapterRef.osis_id, word.group('verse'))),
                position = len(verseRefs),
                parent = chapterRefs[-1],
                numerical_start = word.group('verse'),
                start_token = token
            )
            verseRef.save()
            verseRefs.append(verseRef)
    
    #Save all books, chapterRefs, and verseRefs
    bookRef.end_token = bookTokens[-1]
    bookRef.save()
    chapterRefs[-1].end_token = bookTokens[-1]
    for chapterRef in chapterRefs:
        chapterRef.save()
    verseRefs[-1].end_token = bookTokens[-1]
    for verseRef in verseRefs:
        verseRef.save()
    
    

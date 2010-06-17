# -*- coding: utf8 -*-
# 
# osis.py: Module for repesenting OSIS objects (osisIDs, osisRefs, etc)
# Latest: http://github.com/openscriptures/api/blob/master/osis.py
# 
# Copyright (C) 2010 OpenScriptures.org contributors
# Dual licensed under the MIT or GPL Version 2 licenses.
# 
# MIT License (appears below): http://creativecommons.org/licenses/MIT/
# GPL license: http://creativecommons.org/licenses/GPL/2.0/
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.


# ----
# TODO: Each object should be initializable without any input (empty)
# Each object should also have a stream parser which can be used from the outside

import re
from datetime import date, time, datetime


#TODO: We need a way of creating/storing arbitrary canonical book orders
#TODO: Include facility for converting natural language references into osisRefs?

#BIBLE_BOOK_CODES = (
#    "Gen", "Exod", "Lev", "Num", "Deut", "Josh", "Judg", "Ruth", "1Sam", "2Sam", "1Kgs", "2Kgs", "1Chr", "2Chr", "Ezra", "Neh", "Esth", "Job", "Ps", "Prov", "Eccl", "Song", "Isa", "Jer", "Lam", "Ezek", "Dan", "Hos", "Joel", "Amos", "Obad", "Jonah", "Mic", "Nah", "Hab", "Zeph", "Hag", "Zech", "Mal",
#    "Matt", "Mark", "Luke", "John", "Acts", "Rom", "1Cor", "2Cor", "Gal", "Eph", "Phil", "Col", "1Thess", "2Thess", "1Tim", "2Tim", "Titus", "Phlm", "Heb", "Jas", "1Pet", "2Pet", "1John", "2John", "3John", "Jude", "Rev",
#    "Bar", "AddDan", "PrAzar", "Bel", "SgThree", "Sus", "1Esd", "2Esd", "AddEsth", "EpJer", "Jdt", "1Macc", "2Macc", "3Macc", "4Macc", "PrMan", "Sir", "Tob", "Wis"
#)

#QUESTION: Do these even need to be defined here? Can an exhaustive list of orders be made?
BOOK_ORDERS = {
    "Bible": {
        "KJV": [
            # Old Testament
            "Gen", "Exod", "Lev", "Num", "Deut", "Josh", "Judg", "Ruth", "1Sam", "2Sam", "1Kgs", "2Kgs", "1Chr", "2Chr", "Ezra", "Neh", "Esth", "Job", "Ps", "Prov", "Eccl", "Song", "Isa", "Jer", "Lam", "Ezek", "Dan", "Hos", "Joel", "Amos", "Obad", "Jonah", "Mic", "Nah", "Hab", "Zeph", "Hag", "Zech", "Mal",
            # New Testament
            "Matt", "Mark", "Luke", "John", "Acts", "Rom", "1Cor", "2Cor", "Gal", "Eph", "Phil", "Col", "1Thess", "2Thess", "1Tim", "2Tim", "Titus", "Phlm", "Heb", "Jas", "1Pet", "2Pet", "1John", "2John", "3John", "Jude", "Rev",
            # Deuterocanonical
            "Bar", "AddDan", "PrAzar", "Bel", "SgThree", "Sus", "1Esd", "2Esd", "AddEsth", "EpJer", "Jdt", "1Macc", "2Macc", "3Macc", "4Macc", "PrMan", "Sir", "Tob", "Wis"
        ]
    }
}

#PROBLEM: Osis Book Names are biased toward the KJV tradition?
BOOK_NAMES = {
    "Bible": {
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
}

class OsisWork():
    """
    OSIS work such as Bible.Crossway.ESV.2001 (the part of an osisID before ‘:’)
    
    Organized into period-delimited segments increasingly narrowing in scope.
    
    #TODO: Is this the way to do docstring tests?
    >> work = OsisWork("Bible")
    >> work = OsisWork("ESV")
    >> work = OsisWork("Bible.Crossway.ESV.2001")
    >> work = OsisWork("Bible.BibleOrg.NET.2004.04.01.r123")
    """
    # osisWorkType = ((\p{L}|\p{N}|_)+)((\.(\p{L}|\p{N}|_)+)*)?
    # osisWork = (((\p{L}|\p{N}|_)+)((\.(\p{L}|\p{N}|_)+)*)?:)
    #REGEX = re.compile(ur'''
    #    \w+ (?: \. \w+ )*
    #    
    #    #( \w+ )(?: \. ( \w+ ))*
    #    #(?:
    #    #    (?:(?<!^) \. )?
    #    #    ( \w+ )
    #    #)+
    #''', re.VERBOSE | re.UNICODE)
    # Note: repeating capture groups aren't used because only the last one is accessible
    
    # This list can be modified as needed to add support (recognition) for other types
    TYPES = [
        "Bible",
        #"Quran",
        #"Mishnah",
        #"Talmud",
        #"BookOfMormon",
        # ...
    ]
    
    def __init__(self, *args, **kwargs):
        # Todo: Allow these properties to be set via kwargs!
        
        self.type = None
        self.language = None
        self.publisher = None
        self.name = None
        self.pub_date = None
        self.pub_date_granularity = 6 #1=year, 2=year-month, 3=year-month-day, 4=year-month-day-hour, etc.
        
        self.remaining_input_unparsed = None
        
        # TODO: What if pub_date is later modified? The granularity will need to be re-set
        
        # TODO: Allow the osis_work_str param to not be provided, and for the
        # components to be supplied after init
        
        
        # Parse the input
        if len(args):
            
            segment_regexp = re.compile(ur"""
                (\w+)( \. | $ )
            """, re.VERBOSE | re.UNICODE)
            
            segments = []
            self.remaining_input_unparsed = args[0]
            while len(self.remaining_input_unparsed) > 0:
                matches = segment_regexp.match(self.remaining_input_unparsed)
                if not matches:
                    # Usually error if there is remaining that cannot be parsed
                    if kwargs.get('error_if_remainder', True):
                        raise Exception("Unable to parse string at '%s' for OsisWork: %s" % (self.remaining_input_unparsed, args[0]))
                    # When OsisID invokes OsisWork, it will want to use the remaining
                    else:
                        break
                
                segments.append(matches.group(1))
                self.remaining_input_unparsed = self.remaining_input_unparsed[len(matches.group(0)):]
            
            # Get the type
            if segments[0] in self.TYPES:
                self.type = segments.pop(0)
            
            # Get the language
            if len(segments) and re.match(r'^[a-z]{2,3}\b', segments[0]):
                self.language = segments.pop(0)
            
            # TODO: We need to unescape characters!
            
            # Get the rest of the Get the slugs, publisher and/or shortname 
            segment_slugs = []
            has_remaining_segments = lambda: len(segments) > 0
            while has_remaining_segments(): #for segment in segments:
                #segment = segments.pop(0)
                
                # Find the slugs (e.g. Publisher or Name)
                if re.match(ur"^(?!\d\d)\w+$", segments[0]):
                    segment_slugs.append(segments.pop(0))
                
                # The Date/Time
                elif self.pub_date is None and re.match(r'^\d\d\d\d$', segments[0]):
                    datetime_args = []
                    self.pub_date_granularity = 0
                    
                    datetime_segment_formats = (
                        (
                            'year',
                            r'^\d\d\d\d$',
                            lambda matches: ( int(matches.group(0)), )
                        ),
                        (
                            'month',
                            r'^\d\d$',
                            lambda matches: ( int(matches.group(0)), )
                        ),
                        (
                            'day',
                            r'^\d\d$',
                            lambda matches: ( int(matches.group(0)), )
                        ),
                        (
                            'time',
                            r'^(?P<hours>\d\d)(?P<minutes>\d\d)(?P<seconds>\d\d)?$',
                            lambda matches: (
                                int(matches.group('hours')),
                                int(matches.group('minutes')),
                                int(matches.group('seconds'))
                            )
                        ),
                        #(
                        #    'milliseconds',
                        #    r'^\d+$',
                        #    lambda matches: int(matches.group(0))
                        #),
                    )
                    
                    for format in datetime_segment_formats:
                        
                        # See if the pattern matches but if not stop doing date/time
                        matches = re.match(format[1], segments[0])
                        if matches is None:
                            break
                        
                        #setattr(
                        #    self,
                        #    format[0],
                        #    format[2](matches)
                        #)
                        for arg in format[2](matches):
                            self.pub_date_granularity += 1
                            datetime_args.append( arg )
                        
                        # Segment was parsed, so pop it and see if we continue
                        segments.pop(0)
                        if not has_remaining_segments():
                            break
                    
                    # The datetime segments have been parsed, so make the datetime
                    if len(datetime_args) > 0:
                        # Provide default month and day
                        while len(datetime_args) <3: # Yes, I love you!
                            datetime_args.append(1)
                        
                        self.pub_date = datetime(*datetime_args) #spread!
                    
                else:
                    #TODO: This should glob all unrecognized segments into an etc
                    raise Exception("Unexpected segment: %s" % segment)
            
            # If only one slug, then it's the name
            if len(segment_slugs) == 1:
                self.name = segment_slugs[0]
            # If two slugs, then its publisher followed by name
            elif len(segment_slugs) == 2:
                self.publisher = segment_slugs[0]
                self.name = segment_slugs[1]
            # Otherwise, error!
            elif len(segment_slugs) != 0:
                raise Exception("Unexpected number of segment slugs (%d)! Only 2 are recognized.")
            
            # Now handle revision number, version number, and edition number?
        # end if not len(args)
        
        # Now populate the members via the kwargs
        #for key in ('type', 'language', 'publisher', 'name', 'pub_date', 'pub_date_granularity'):
        #setattr(self, key, kwargs[key])
        if kwargs.has_key('type'):
            self.type = str(kwargs['type'])
            
        if kwargs.has_key('language'):
            self.language = str(kwargs['language'])
            
        if kwargs.has_key('publisher'):
            self.publisher = str(kwargs['publisher'])
            
        if kwargs.has_key('name'):
            self.name = str(kwargs['name'])
            
        if kwargs.has_key('pub_date'):
            if isinstance(kwargs['pub_date'], datetime):
                self.pub_date = kwargs['pub_date']
            else:
                #self.pub_date = datetime.strptime(str(kwargs['pub_date']), "%Y-%m-%dT%H:%M:%S.Z")
                raise Exception("pub_date must be a datetime object")
        
        if kwargs.has_key('pub_date_granularity'):
            self.pub_date_granularity = int(kwargs['pub_date_granularity'])
            
        
        if __name__ == "__main__":
            print "OsisWork(%s)" % str(self)
    
    def get_segments(self):
        segments = []
        
        if self.type is not None:
            segments.append(self.type)
        
        if self.language is not None:
            segments.append(self.language)
        
        if self.publisher is not None:
            segments.append(self.publisher)
        
        if self.name is not None:
            segments.append(self.name)
        
        if self.pub_date is not None:
            date_parts = (
                'year',
                'month',
                'day',
            )
            for i in range(0, min( len(date_parts), self.pub_date_granularity )):
                segments.append( "%02d" % getattr(self.pub_date, date_parts[i]) )
            
            time_parts = (
                'hour',
                'minute',
                'second'
            )
            time = ""
            for i in range(0, min( len(time_parts), self.pub_date_granularity - 3 )):
                #segments.append( "%02d" % getattr(self.pub_date, time_parts[i]) )
                time += "%02d" % getattr(self.pub_date, time_parts[i])
            if time != "":
                segments.append(time)
        return segments
    segments = property(get_segments)
    
    def __str__(self):
        return ".".join(self.segments)


class OsisSegmentList():
    """
    Used for OsisPassage.identifier and OsisPassage.subidentifier
    Potentially could also be used for OsisWork.
    """
    
    def __init__(self, segment_str = ""):
        self.segments = []
        
        segment_regex = re.compile(ur"""
            (?P<segment>   (?: \w | \\\S )+ )
            (?P<delimiter>     \. | $     )
        """, re.VERBOSE | re.UNICODE)

        remaining_segment_str = segment_str
        while len(remaining_segment_str) > 0:
            matches = segment_regex.match(remaining_segment_str)
            if not matches:
                raise Exception("Unxpected string at '%s' in '%s'" % (remaining_segment_str, segment_str))
            segment = matches.group('segment')
            
            # Remove escapes
            segment = segment.replace("\\", "")
            self.segments.append(segment)
            
            remaining_segment_str = remaining_segment_str[len(matches.group(0)):]
        
    def __str__(self):
        return ".".join(
            map(
                lambda segment: re.sub(ur"(\W)", ur"\\\1", str(segment)),
                self.segments
            )
        )
    
    


class OsisPassage():
    """
    OSIS passage such as Exodus.3.8 (i.e. without the work prefix)
    
    Organized into period-delimited segments increasingly narrowing in scope,
    followed by an optional sub-identifier which is work-specific. Segments
    usually consist of an alpha-neumeric book code followed by a chapter number
    and a verse number. While there are conventions for book names, they are not
    standardized and one system is not inherently preferable over another, as
    the goal is to affirm canon-neutrality. Likewise, there is nothing
    restricting the segments to a single book, chapter, and verse identifier.
    There may be a book volumn identifier, or alphabetical chapters, or even
    numbered paragraph segments.
    
    Read what Chris Little of Crosswire says:
    http://groups.google.com/group/open-scriptures/msg/4fb744efb27c1a41?pli=1
    """
    
    # Work: (((\p{L}|\p{N}|_)+)((\.(\p{L}|\p{N}|_)+)*)?:)?
    
    # Passage: ((\p{L}|\p{N}|_|(\\[^\s]))+)((\.(\p{L}|\p{N}|_|(\\[^\s]))+)*)?
    # Subidentifiers: (!((\p{L}|\p{N}|_|(\\[^\s]))+)((\.(\p{L}|\p{N}|_|(\\[^\s]))+)*)?)? 
    
    #REGEX = re.compile(ur"""
    #    (
    #        {segment}(?:\.{segment})*
    #    )
    #    
    #    # OSIS Manual: “Translations also often split verses into parts,
    #    # provided labels such as ‘a’ and ‘b’ for the separate parts. Encoders
    #    # may freely add sub-identifiers below the lowest standardized level.
    #    # They are set off from the standardized portion by the character ‘!’.”
    #    (?:!
    #        (
    #            {segment}(?:\.{segment})*
    #        )
    #    )?
    #""".format(
    #    segment= ur"(?:\w|\\\S)+"
    #), re.VERBOSE | re.UNICODE)
    
    def __init__(self, osis_passage_str = ""):
        
        if __name__ == "__main__":
            print "OsisPassage(%s)" % osis_passage_str
        
        # It's ok to have an empty passage (it can be built later)
        if not osis_passage_str:
            self.identifier = OsisSegmentList()
            self.subidentifier = OsisSegmentList()
            return
        
        # This regular expression need not be 
        #segment_regex = re.compile(r"""
        #    (?P<identifier>.+?)
        #    (?:
        #        !
        #        (?P<subidentifier>.+?)
        #    )
        #""", re.VERBOSE | re.UNICODE)
        #
        #matches = segment_regex.match(osis_passage_str)
        #if not matches:
        #    raise Exception("Unable to parse out identifier and subidentifier from %s" % osis_passage_str)
        passage_parts = osis_passage_str.split("!", 2)
        self.identifier = OsisSegmentList(passage_parts[0])
        
        if len(passage_parts) == 2:
            self.subidentifier = OsisSegmentList(passage_parts[1])
        else:
            self.subidentifier = OsisSegmentList()
        
        return
        
        # Parse the segments out of the string
        #in_subidentifier = False
        #remaining_str = osis_passage_str
        #while len(remaining_str) > 0:
        #    matches = segment_regex.match(remaining_str)
        #    if not matches:
        #        raise Exception("Unxpected string at '%s' in '%s'" % (remaining_str, osis_passage_str))
        #    segment = matches.group('segment')
        #    
        #    # Remove escapes
        #    segment = segment.replace("\\", "")
        #    
        #    if in_subidentifier:
        #        self.subsegments.append(segment)
        #    else:
        #        self.segments.append(segment)
        #    
        #    if matches.group('delimiter') == '!':
        #        # If we're already in the subidentifier, then it's a syntax error
        #        if in_subidentifier:
        #            raise Exception("Unxpected second '!' in '%s'" % (osis_passage_str))
        #        in_subidentifier = True
        #    
        #    remaining_str = remaining_str[len(matches.group(0)):]
        
        
        #matches = self.SEGMENT_REGEX.match(osis_passage_str)
        #print "osis_work_str = ", osis_work_str
        #print matches.endpos-1 , len(osis_work_str)
        #if not matches or len(matches.group(0)) != len(osis_passage_str):
        #    raise Exception("Unable to parse string as a OsisPassage: %s" % osis_passage_str)
        
        #self.segments = osis_passage_str.split('.') #temp

    
    
    #def get_identifier(self):
    #    return ".".join(
    #        map(
    #            lambda segment: re.sub(ur"(\W)", ur"\\\1", str(segment)),
    #            self.segments
    #        )
    #    )
    #identifier = property(get_identifier)
    #
    #def get_subidentifier(self):
    #    return ".".join(
    #        map(
    #            lambda subsegment: re.sub(ur"(\W)", ur"\\\1", str(subsegment)),
    #            self.subsegments
    #        )
    #    )
    #subidentifier = property(get_subidentifier)
    
    def __str__(self):
        #identifier = ".".join(
        #    map(
        #        lambda segment: re.sub(ur"(\W)", ur"\\\1", segment),
        #        self.segments
        #    )
        #)
        #
        #subidentifier = ".".join(
        #    map(
        #        lambda subsegment: re.sub(ur"(\W)", ur"\\\1", subsegment),
        #        self.subsegments
        #    )
        #)
        repr = str(self.identifier)
        if len(self.subidentifier.segments) > 0:
            repr += "!" + str(self.subidentifier)
        return repr


class OsisID():
    """
    An osisID which represents a passage within a single work like ESV:Exodus.1
    Includes a work prefix (OsisWork) and/or a passage (OsisPassage).
    """
#    REGEX = re.compile(
#        ur"""
#            #^
#            (?:
#                (?P<work>{work})
#                :
#            )?
#            
#            (?P<passage>{passage})?
#            
#            #$
#        """.format(
#            work = OsisWork.REGEX.pattern,
#            passage = OsisPassage.REGEX.pattern
#    ), re.VERBOSE | re.UNICODE)
    
    def __init__(self, osis_id_str = ""):
        
        self.work = OsisWork()
        
        
        
        self.passage = OsisPassage()
        
        # Consists of OsisWork + OsisPassage
        pass
        
#        #osisIDRegExp = re.compile(OSIS_ID_REGEX, re.VERBOSE | re.UNICODE)
#        
#        self.work = None
#        self.passage = None
#        
#        matches = self.REGEX.match(id)
#        if not matches:
#            raise Exception("Unable to parse osisID: " + osis_id_str)
#        
#        
#        
#        print matches.groups()
#        print matches.groupdict()
#        
#        #assert(matches)
#
#
#class OsisRef():
#    """
#    An osisRef which can contain a single passage from a work or a passage range from a work
#    """
#    #(@(cp\[(\p{Nd})*\]|s\[(\p{L}|\p{N})+\](\[(\p{N})+\])?))?
#    start = None
#    end = None
#    
#    
#    #(((\p{L}|\p{N}|_)+)((\.(\p{L}|\p{N}|_)+)*)?:)?((\p{L}|\p{N}|_|(\\[^\s]))+)(\.(\p{L}|\p{N}|_|(\\[^\s]))*)*(!((\p{L}|\p{N}|_|(\\[^\s]))+)((\.(\p{L}|\p{N}|_|(\\[^\s]))+)*)?)?(@(cp\[(\p{Nd})*\]|s\[(\p{L}|\p{N})+\](\[(\p{N})+\])?))?(\-((((\p{L}|\p{N}|_|(\\[^\s]))+)(\.(\p{L}|\p{N}|_|(\\[^\s]))*)*)+)(!((\p{L}|\p{N}|_|(\\[^\s]))+)((\.(\p{L}|\p{N}|_|(\\[^\s]))+)*)?)?(@(cp\[(\p{Nd})*\]|s\[(\p{L}|\p{N})+\](\[(\p{N})+\])?))?)?
#    
#    def __init__(self, osis_ref_str):
#        raise Exception("Not implemented")
#    


#### DEPRECATED!!! #####
def parse_osis_ref(osis_ref_string):
    """
    DEPRECATED. Use OsisRef object instead?
    """
    #TODO: This should instead return a list of OsisRef objects
    
    
    parser = re.compile(ur"""
        ^(?:
            (?P<work_prefix>[^:]+?)(?: : | $ )
        )?
        (?P<start_osis_id>
            (?!-)
            .+?
        )?
        (?:-
            (?P<end_osis_id>.+? )
        )?$
    """, re.VERBOSE)
    match = parser.match(osis_ref_string)
    if not match:
        raise Exception("Unable to parse osisRef")
    if not match.group('work_prefix') and not match.group('start_osis_id'):
        raise Exception("Must have either work_prefix or osis_id")
    if not match.group('start_osis_id') and match.group('end_osis_id'):
        raise Exception("If having an end osisID, you must have a start.")
    
    result = {
        'groups':match.groupdict(),
        'work_prefix':None,
        'start_osis_id':None,
        'end_osis_id':None
    }
    
    
    # Get work_prefix
    if match.group('work_prefix'):
        work_prefix = {
            #'original':match.group('work_prefix'),
            #'type':None,
            #'language':None,
            #'publisher':None,
            #'osis_slug':None,
            #'publish_date':None
        }
        
        parts = match.group('work_prefix').split('.')
        
        # Get the TYPE
        if parts[0] in TYPES:
            work_prefix['type'] = parts.pop(0)
        
        slugs = []
        for part in parts:
            # Get the year
            if not work_prefix.has_key('publish_date') and re.match(r'^\d\d\d\d$', part):
                work_prefix['publish_date'] = part  #date(int(part), 1, 1)
            
            # Get the language
            elif not work_prefix.has_key('language') and re.match(r'^[a-z]{2,3}\b', part):
                work_prefix['language'] = part
            
            # Get the slugs
            elif re.match(r'^\w+$', part):
                slugs.append(part)
            
            # Unrecognized 
            else:
                raise Exception("Unexpected OSIS work prefix component: " + part)
        
        # Get the osis_slug and publisher
        if len(slugs) == 1:
            work_prefix['osis_slug'] = slugs[0]
        elif len(slugs) == 2:
            work_prefix['publisher'] = slugs[0]
            work_prefix['osis_slug'] = slugs[1]
        elif len(slugs) != 0:
            raise Exception("Unexpected slug count in OSIS work prefix: " + str(work_prefix))
        
        result['work_prefix'] = work_prefix
    
    # Parse the start_osis_id and end_osis_id
    parser = re.compile(ur"""
        ^
        (?P<book>[^\.]+?)
        (?:\.(?P<chapter>[^\.]+?))?
        (?:\.(?P<verse>[^\.]+?))?
        # TODO: Add the grains too
        $
    """, re.VERBOSE)
    
    # Start osisID
    if match.group('start_osis_id'):
        id_match = parser.match(match.group('start_osis_id'))
        if not id_match:
            raise Exception("Invalid osisID: " + match.group('start_osis_id'))
        result['start_osis_id'] = id_match.groupdict()
        result['start_osis_id']['original'] = match.group('start_osis_id')
        
    # End osisID
    if match.group('end_osis_id'):
        id_match = parser.match(match.group('end_osis_id'))
        if not id_match:
            raise Exception("Invalid osisID: " + match.group('end_osis_id'))
        result['end_osis_id'] = id_match.groupdict()
        result['end_osis_id']['original'] = match.group('end_osis_id')
    
    return result




# Tests
if __name__ == "__main__":
    import sys
    
    # Test OsisWork ########################################
    print "Testing OsisWork...";
    
    work = OsisWork("Bible")
    assert(work.type == "Bible")
    assert(str(work) == "Bible")
    assert("Bible" == str(work))
    
    work = OsisWork("KJV")
    assert(work.type is None)
    assert(work.name == "KJV")
    print work
    assert("KJV" == str(work))
    
    work = OsisWork("Bible.en")
    assert(work.type == "Bible")
    assert(work.language == "en")
    assert("Bible.en" == str(work))
    
    work = OsisWork("Bible.en.KJV")
    assert(work.type == "Bible")
    assert(work.language == "en")
    assert(work.name == "KJV")
    assert("Bible.en.KJV" == str(work))
    
    work = OsisWork("Bible.en.KJV.1611")
    assert(work.language == "en")
    assert(work.name == "KJV")
    assert(work.pub_date.year == 1611)
    assert("Bible.en.KJV.1611" == str(work))
    
    work = OsisWork("Bible.en.ChurchOfEngland.KJV.1611")
    assert(work.type == "Bible")
    assert(work.language == "en")
    assert(work.publisher == "ChurchOfEngland")
    assert(work.name == "KJV")
    assert(work.pub_date.year == 1611)
    assert("Bible.en.ChurchOfEngland.KJV.1611" == str(work))
    work.publisher = None
    work.name = "Steph"
    work.pub_date = work.pub_date.replace(year = 1500)
    assert("Bible.en.Steph.1500" == str(work))
    
    work = OsisWork("KJV.1611.06.07")
    #work = OsisWork("KJV.1611-06-07")
    assert(work.name == "KJV")
    assert(work.pub_date.year == 1611)
    assert(work.pub_date.month == 6)
    assert(work.pub_date.day == 7)
    assert(work.pub_date.isoformat() == "1611-06-07T00:00:00")
    assert("KJV.1611.06.07" == str(work))
    
    work = OsisWork("KJV.1611.06.07.235930")
    assert(work.pub_date.isoformat() == "1611-06-07T23:59:30")
    assert("KJV.1611.06.07.235930" == str(work))
    work.pub_date = work.pub_date.replace(year=2001, hour=0)
    work.pub_date_granularity = 6
    assert("KJV.2001.06.07.005930" == str(work))
    work.pub_date_granularity = 5
    assert("KJV.2001.06.07.0059" == str(work))
    work.pub_date_granularity = 4
    assert("KJV.2001.06.07.00" == str(work))
    work.pub_date_granularity = 3
    assert("KJV.2001.06.07" == str(work))
    work.pub_date_granularity = 2
    assert("KJV.2001.06" == str(work))
    work.pub_date_granularity = 1
    assert("KJV.2001" == str(work))
    work.pub_date_granularity = 0
    assert("KJV" == str(work))
    
    work = OsisWork()
    assert(str(work) == "")
    
    work = OsisWork(
        type = "Bible",
        language = "en-US",
        publisher = "Baz",
        name = "WMR",
        pub_date = datetime(1611, 1, 1),
        pub_date_granularity = 1 #year
    )
    assert(work.type == "Bible")
    assert(work.language == "en-US")
    assert(work.publisher == "Baz")
    assert(work.name == "WMR")
    assert(work.pub_date.year == 1611)
    assert("Bible.en-US.Baz.WMR.1611" == str(work))
    
    work = OsisWork("Bible.Baz.WMR.1611",
        language = "en-UK",
        pub_date = datetime(2000,2,1),
        pub_date_granularity = 2
    )
    assert("Bible.en-UK.Baz.WMR.2000.02" == str(work))
    
    
    # Test OsisPassage ########################################
    passage = OsisPassage("John.3.16")
    assert(len(passage.identifier.segments) == 3)
    print str(passage)
    assert("John.3.16" == str(passage))
    
    passage = OsisPassage("John")
    assert(len(passage.identifier.segments) == 1)
    passage.identifier.segments.append("17")
    assert(len(passage.identifier.segments) == 2)
    assert("John.17" == str(passage))
    
    passage = OsisPassage("John.A.B\.C\.D")
    assert(passage.identifier.segments[0] == "John")
    assert(passage.identifier.segments[1] == "A")
    assert(passage.identifier.segments[2] == "B.C.D")
    
    # Test subidentifier
    passage = OsisPassage("John.3.16!b")
    print passage
    assert(passage.subidentifier.segments[0] == "b")
    passage.subidentifier.segments[0] = "a"
    assert("John.3.16!a" == str(passage))
    assert(str(passage.subidentifier) == "a")
    passage.subidentifier.segments.append(1);
    assert(str(passage.subidentifier) == "a.1")
    passage.subidentifier.segments.pop();
    passage.subidentifier.segments.append("2");
    assert(str(passage.subidentifier) == "a.2")
    
    # Test identifier
    assert(str(passage.identifier) == "John.3.16")
    passage.identifier.segments.pop()
    passage.identifier.segments.append("Hello World!")
    assert(str(passage.identifier) == r"John.3.Hello\ World\!")
    
    passage = OsisPassage()
    assert(str(passage) == "")
    
    #assert(passage.book == "John")
    #assert(passage.chapter == "3")
    #assert(passage.verse == "16")
    
    #exit()
    #bad_works = [
    #    "@#$%^&",
    #    "Bible.Hello World Bible Society.NonExistantTranslation"
    #]
    #for work in bad_works:
    #    try:
    #        obj = OsisWork(work)
    #        raise Exception(True)
    #    except:
    #        assert(sys.exc_value is not True)
    #
    #exit()
    #
    ## Test full osisID
    ##osisIDRegExp = re.compile(OSIS_ID_REGEX, re.VERBOSE | re.UNICODE)
    #ok_passages = [
    #    "John.1",
    #    "John.1.13",
    #    "John.A.13",
    #    "John.A.B.C.D",
    #    "John.A.B\.C\.D",
    #    "Bible:John.1",
    #    "Bible.KJV:John.1",
    #    "Bible.KJV.1611:John.1",
    #    "Bible.ChurchOfEngland.KJV.1611:John.1",
    #    
    #    "Esth.1.1!note.c",
    #    "Esth.1.1!crossReference"
    #]
    #for passage in ok_passages:
    #    passage = OsisPassage(passage)
    #    
    #    #matches = osisIDRegExp.match(id)
    #    #assert(matches)
    #    #print id, matches.groups()
    #
    ## Test OsisID object
    
    
    # Test osisRef (extended)
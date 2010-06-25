# -*- coding: utf8 -*-
"""
Module for repesenting OSIS objects (osisIDs, osisRefs, etc)

Latest: http://github.com/openscriptures/api/blob/master/osis.py
Copyright (C) 2010 OpenScriptures.org contributors
Dual licensed under the MIT or GPL Version 2 licenses.
MIT License: http://creativecommons.org/licenses/MIT/
GPL 2.0 license: http://creativecommons.org/licenses/GPL/2.0/
"""

# MIT License:
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

__credits__ = [
    "Weston Ruter"
]
__copyright__ = "Copyright 2010, Open Scriptures"
__license__ = "GPL 2.0 or MIT"
__version_info__ = (0,1)
__version__ = ".".join([str(part) for part in __version_info__ ])
__status__ = "Development"


# ----
# TODO: When passing in objects to kwargs, make sure that we do deepcopy?
# TODO: Ideally there would be setters for properties which would allow both:
#         id.work = OsisWork("Bible.KJV")
#         id.work = "Bible.KJV"
#       The second of which would get casted into an OsisWork; this can be done
#       with a private dict containing values, but exposing getter/setter UI
# TODO: OsisWork may not be properly implemented according to the spec; it may need to just be a SegmentList (without escapes)
#       Can work's languages contain hyphens?

# TODO: potentially refactor out common patterns in classes; improve consistency
# TODO: use better names than "unparsed_input" and "error_if_remainder" and "remaining_input_unparsed"


import re
import copy
import sys
from datetime import date, time, datetime

#TODO: We need a way of creating/storing arbitrary canonical book orders
#TODO: Include facility for converting natural language references into osisRefs?

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

# PROBLEM: Osis Book Names are biased toward the KJV tradition and they're
# definitely English; this needs to be part of a separate canon-specific module
# which also handles the parsing and generating of locale-specific references.

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

class OsisError(Exception):
    """Base class for errors in the OSIS module."""


class OsisWork():
    """
    OSIS work such as Bible.Crossway.ESV.2001 (the part of an osisID before ‘:’)
    
    Organized into period-delimited segments increasingly narrowing in scope.
    Currently, the required sequence is:
     1. type
     2. language
     3. publisher
     4. name
     5. pub_date
    All of these fields are optional.
    
    Note that this probably is the incorrect way to implement this model.
    Namely, the name might need to go before publisher, and the whole OsisWork
    may need to extend SegmentList just like OsisPassage does (twice).
    The members listed above would then by dynamic getters which would retrieve
    items from the segment list.
    
    Schema regexp: ((\p{L}|\p{N}|_)+)((\.(\p{L}|\p{N}|_)+)*)?

    >>> work = OsisWork("Bible")
    >>> assert work.type == "Bible"
    >>> assert str(work) == "Bible"
    >>> assert "Bible" == str(work)
    
    >>> work = OsisWork("KJV")
    >>> assert work.type is None
    >>> assert work.name == "KJV"
    >>> assert "KJV" == str(work)

    >>> work = OsisWork("Bible.en.KJV")
    >>> assert work.type == "Bible"
    >>> assert work.language == "en"
    >>> assert work.name == "KJV"
    >>> assert "Bible.en.KJV" == str(work)
    
    >>> work = OsisWork("Bible.en.KJV.1611")
    >>> assert work.language == "en"
    >>> assert work.name == "KJV"
    >>> assert work.pub_date.year == 1611
    >>> assert "Bible.en.KJV.1611" == str(work)
    
    >>> work = OsisWork("Bible.en.ChurchOfEngland.KJV.1611")
    >>> assert work.type == "Bible"
    >>> assert work.language == "en"
    >>> assert work.publisher == "ChurchOfEngland"
    >>> assert work.name == "KJV"
    >>> assert work.pub_date.year == 1611
    >>> assert "Bible.en.ChurchOfEngland.KJV.1611" == str(work)
    >>> work.publisher = None
    >>> work.name = "Steph"
    >>> work.pub_date = work.pub_date.replace(year = 1500)
    >>> assert "Bible.en.Steph.1500" == str(work)
    
    >>> work = OsisWork("KJV.1611.06.07")
    >>> assert work.name == "KJV"
    >>> assert work.pub_date.year == 1611
    >>> assert work.pub_date.month == 6
    >>> assert work.pub_date.day == 7
    >>> assert work.pub_date.isoformat() == "1611-06-07T00:00:00"
    >>> assert "KJV.1611.06.07" == str(work)
    
    >>> work = OsisWork("KJV.1611.06.07.235930")
    >>> assert work.pub_date.isoformat() == "1611-06-07T23:59:30"
    >>> assert "KJV.1611.06.07.235930" == str(work)
    >>> work.pub_date = work.pub_date.replace(year=2001, hour=0)
    >>> work.pub_date_granularity = 6
    >>> assert "KJV.2001.06.07.005930" == str(work)
    >>> work.pub_date_granularity = 5
    >>> assert "KJV.2001.06.07.0059" == str(work)
    >>> work.pub_date_granularity = 4
    >>> assert "KJV.2001.06.07.00" == str(work)
    >>> work.pub_date_granularity = 3
    >>> assert "KJV.2001.06.07" == str(work)
    >>> work.pub_date_granularity = 2
    >>> assert "KJV.2001.06" == str(work)
    >>> work.pub_date_granularity = 1
    >>> assert "KJV.2001" == str(work)
    >>> work.pub_date_granularity = 0
    >>> assert "KJV" == str(work)
    
    >>> work = OsisWork()
    >>> assert str(work) == ""
    
    >>> work = OsisWork(
    ...     type = "Bible",
    ...     language = "en-US",
    ...     publisher = "Baz",
    ...     name = "WMR",
    ...     pub_date = datetime(1611, 1, 1),
    ...     pub_date_granularity = 1 #year
    ... )
    >>> assert work.type == "Bible"
    >>> assert work.language == "en-US"
    >>> assert work.publisher == "Baz"
    >>> assert work.name == "WMR"
    >>> assert work.pub_date.year == 1611
    >>> assert "Bible.en-US.Baz.WMR.1611" == str(work)
    
    >>> work = OsisWork("Bible.Baz.WMR.1611",
    ...    language = "en-UK",
    ...    pub_date = datetime(2000,2,1),
    ...    pub_date_granularity = 2
    ... )
    >>> assert "Bible.en-UK.Baz.WMR.2000.02" == str(work)
    
    >>> work = OsisWork(
    ...     type = "Bible",
    ...     language = "en-UK",
    ...     pub_date = "1992-01-03"
    ... )
    >>> assert "Bible.en-UK.1992.01.03" == str(work)
    >>> work.pub_date_granularity = 2
    >>> assert "Bible.en-UK.1992.01" == str(work)
    
    >>> work = OsisWork("Bible.en remainder1", error_if_remainder = False)
    >>> assert str(work) == "Bible.en"
    >>> try:
    ...     work = OsisWork("Bible.en remainder2", error_if_remainder = True)
    ...     raise Exception(True)
    ... except:
    ...     assert sys.exc_value is not True
    """
    
    # This list can be modified as needed to add support (recognition) for other types
    TYPES = [
        "Bible",
        #"Quran",
        #"Mishnah",
        #"Talmud",
        #"BookOfMormon",
        # ...
    ]
    
    # Todo: It would be better if this was a SegmentList and that the various properties were dynamically discovered on get?
    def __init__(self, unparsed_input = "", **kwargs):
        self.type = None
        self.language = None
        self.publisher = None
        self.name = None
        self.pub_date = None
        self.pub_date_granularity = 6 #1=year, 2=year-month, 3=year-month-day, 4=year-month-day-hour, etc.
        
        self.remaining_input_unparsed = ""
        error_if_remainder = kwargs.get('error_if_remainder', True)
        
        # Parse the input
        if unparsed_input:
            
            segment_regexp = re.compile(ur"""
                (?P<segment>    \w+    )
                (?P<delimiter> \. | $ )?
            """, re.VERBOSE | re.UNICODE)
            
            segments = []
            self.remaining_input_unparsed = unparsed_input
            while len(self.remaining_input_unparsed) > 0:
                matches = segment_regexp.match(self.remaining_input_unparsed)
                if not matches:
                    # Usually error if there is remaining that cannot be parsed
                    if error_if_remainder:
                        raise OsisError("Unable to parse string at '%s' for OsisWork: %s" % (self.remaining_input_unparsed, unparsed_input))
                    # When OsisID invokes OsisWork, it will want to use the remaining
                    else:
                        break
                
                segments.append(matches.group("segment"))
                self.remaining_input_unparsed = self.remaining_input_unparsed[len(matches.group(0)):]
                
                # Handle case where no ending delimiter was found
                if matches.group("delimiter") is None:
                    if error_if_remainder:
                        raise OsisError("Expected ending delimiter at '%s' for OsisWork: %s" % (self.remaining_input_unparsed, unparsed_input))
                    else:
                        break
            
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
                        while len(datetime_args) <3: # Yes, I ♥ you!
                            datetime_args.append(1)
                        
                        self.pub_date = datetime(*datetime_args) #spread!
                    
                else:
                    #TODO: This should glob all unrecognized segments into an etc
                    raise OsisError("Unexpected segment: %s" % segment)
            
            # If only one slug, then it's the name
            if len(segment_slugs) == 1:
                self.name = segment_slugs[0]
            # If two slugs, then its publisher followed by name
            elif len(segment_slugs) == 2:
                self.publisher = segment_slugs[0]
                self.name = segment_slugs[1]
            # Otherwise, error!
            elif len(segment_slugs) != 0:
                raise OsisError("Unexpected number of segment slugs (%d)! Only 2 are recognized.")
            
            # Now handle revision number, version number, and edition number?
        # end if not len(args)
        
        # Allow members to be passed in discretely
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
                matches = re.match(r"(\d\d\d\d)-?(\d\d)?-?(\d\d)?[T ]?(\d\d)?:?(\d\d)?:?(\d\d)?$", str(kwargs['pub_date']))
                if not matches:
                    raise OsisError("pub_date passed as a string must be in ISO format (e.g. YYYY-MM-DDTHH:MM:SS)")
                
                # Retreive date values from match groups and determine granularity
                self.pub_date_granularity = 0
                groups = []
                for group in matches.groups():
                    if group is None:
                        break
                    groups.append(int(group))
                    self.pub_date_granularity += 1
                
                # datetime objects must have values for
                while len(groups) <3: # Yes, I ♥ you indeed!
                    groups.append(1)
                self.pub_date = datetime(*groups)
                #self.pub_date = datetime.strptime(str(kwargs['pub_date']), "%Y-%m-%dT%H:%M:%S.Z")
        
        if kwargs.has_key('pub_date_granularity'):
            self.pub_date_granularity = int(kwargs['pub_date_granularity'])
    
    #NOTE: if OsisWork extends SegmentList, this obviously won't be necessary
    def get_segments(self):
        segments = [] #This should be a SegmentList; except segments can't have unescaped segments! i.e. language identifier
        
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
    
    
    def __lt__(self, other):
        return str(self) < str(other)
    def __le__(self, other):
        return str(self) <= str(other)
    def __eq__(self, other):
        return str(self) == str(other)
    def __ne__(self, other):
        return str(self) != str(other)
    def __gt__(self, other):
        return str(self) > str(other)
    def __ge__(self, other):
        return str(self) >= str(other)
    def __cmp__(self, other):
        return cmp(str(self), str(other))
    def __hash__(self):
        return hash(str(self))
    def __nonzero__(self):
        return bool(str(self))
    
    def __repr__(self):
        return "%s<%s>" % (self.__class__.__name__, self)
    def __unicode__(self):
        return ".".join(self.segments)
    def __str__(self):
        return unicode(self).encode('utf-8')


class OsisPassage():
    """
    OSIS passage such as Exodus.3.8: an osisID without the the work prefix.
    
    Organized into period-delimited segments increasingly narrowing in scope,
    followed by an optional sub-identifier which is work-specific. Segments
    usually consist of an alphanumeric book code followed by a chapter number
    and a verse number. While there are conventions for book names, they are not
    standardized and one system is not inherently preferable over another, as
    the goal is to affirm canon-neutrality. Likewise, there is nothing
    restricting the segments to a single book, chapter, and verse identifier.
    There may be a book volumn identifier, or alphabetical chapters, or even
    numbered paragraph segments.
    
    Read what Chris Little of Crosswire says:
    http://groups.google.com/group/open-scriptures/msg/4fb744efb27c1a41?pli=1
    
    OSIS Manual: “Translations also often split verses into parts,
    provided labels such as ‘a’ and ‘b’ for the separate parts. Encoders
    may freely add sub-identifiers below the lowest standardized level.
    They are set off from the standardized portion by the character ‘!’.”
    
    Schema Regexp:
    identifier: ((\p{L}|\p{N}|_|(\\[^\s]))+)((\.(\p{L}|\p{N}|_|(\\[^\s]))+)*)?
    subidentifier: (!((\p{L}|\p{N}|_|(\\[^\s]))+)((\.(\p{L}|\p{N}|_|(\\[^\s]))+)*)?)?
    
    >>> passage = OsisPassage("John.3.16")
    >>> assert len(passage.identifier) == 3
    >>> assert "John.3.16" == str(passage)
    
    >>> passage = OsisPassage("John")
    >>> assert len(passage.identifier) == 1
    >>> passage.identifier.append("17")
    >>> assert len(passage.identifier) == 2
    >>> assert "John.17" == str(passage)
    
    >>> passage = OsisPassage("John.A.B\.C\.D")
    >>> assert passage.identifier[0] == "John"
    >>> assert passage.identifier[1] == "A"
    >>> assert passage.identifier[2] == "B.C.D"
    
    >>> # Try different ways of passing in kwargs
    >>> passage = OsisPassage(
    ...     identifier = "John.2.1",
    ...     subidentifier = "a"
    ... )
    >>> assert str(passage) == "John.2.1!a"
    
    >>> passage = OsisPassage(
    ...     identifier = SegmentList("John.2.1"),
    ...     subidentifier = SegmentList(
    ...         segments = ["a"]
    ...     )
    ... )
    >>> assert str(passage) == "John.2.1!a"
    
    >>> passage = OsisPassage(
    ...     identifier = ["John", 2],
    ...     subidentifier = ("a", "1")
    ... )
    >>> assert str(passage) == "John.2!a.1"
    
    >>> # Test subidentifier
    >>> passage = OsisPassage("John.3.16!b")
    >>> assert passage.subidentifier[0] == "b"
    >>> passage.subidentifier[0] = "a"
    >>> assert "John.3.16!a" == str(passage)
    >>> assert str(passage.subidentifier) == "a"
    >>> passage.subidentifier.append(1)
    >>> assert str(passage.subidentifier) == "a.1"
    >>> assert passage.subidentifier.pop() == 1
    >>> passage.subidentifier.append("2");
    >>> assert str(passage.subidentifier) == "a.2"
    
    >>> # Test identifier
    >>> assert str(passage.identifier) == "John.3.16"
    >>> assert passage.identifier.pop() == "16"
    >>> passage.identifier.append("Hello World!")
    >>> assert str(passage.identifier) == r"John.3.Hello\ World\!"
    
    >>> passage = OsisPassage("John", subidentifier = "abc")
    >>> assert str(passage) == r"John!abc"
    >>> assert str(passage.subidentifier) == r"abc"
    
    >>> passage = OsisPassage()
    >>> assert str(passage) == ""
    
    >>> passage = OsisPassage("John.3!a remainder1", error_if_remainder = False)
    >>> assert str(passage) == "John.3!a"
    >>> try:
    ...     passage = OsisPassage("John.3!a remainder2", error_if_remainder = True)
    ...     raise Exception(True)
    ... except:
    ...     assert sys.exc_value is not True
    """    
    
    def __init__(self, unparsed_input = "", **kwargs):
        error_if_remainder = kwargs.get('error_if_remainder', True)
        self.remaining_input_unparsed = ""
        
        if unparsed_input:
            #passage_parts = unparsed_input.split("!", 2)
            self.identifier = SegmentList(unparsed_input, error_if_remainder = False)
            self.remaining_input_unparsed = self.identifier.remaining_input_unparsed
            if self.remaining_input_unparsed.startswith('!'):
                self.remaining_input_unparsed = self.remaining_input_unparsed[1:]
                self.subidentifier = SegmentList(self.remaining_input_unparsed, error_if_remainder = False)
                self.remaining_input_unparsed = self.subidentifier.remaining_input_unparsed
            else:
                self.subidentifier = SegmentList()
            
            # Handle case where no ending delimiter was found
            if error_if_remainder and len(self.remaining_input_unparsed) > 0:
                raise OsisError("Expected ending delimiter at '%s' for OsisPassage: %s" % (self.remaining_input_unparsed, unparsed_input))
            
        else:
            self.identifier = SegmentList()
            self.subidentifier = SegmentList()
        
        # Allow members to be passed in discretely
        if kwargs.has_key('identifier'):
            #if isinstance(kwargs['identifier'], SegmentList):
            #    self.identifier = kwargs['identifier'] #TODO: copy?
            if hasattr(kwargs['identifier'], "__iter__"):  #isinstance(kwargs['identifier'], list)
                self.identifier = SegmentList(
                    segments = kwargs['identifier'] #TODO: copy?
                )
            else:
                self.identifier = SegmentList(str(kwargs['identifier']))
        
        if kwargs.has_key('subidentifier'):
            #if isinstance(kwargs['subidentifier'], SegmentList):
            #    self.subidentifier = kwargs['subidentifier'] #TODO: copy?
            if hasattr(kwargs['subidentifier'], "__iter__"):  #isinstance(kwargs['identifier'], list)
                self.subidentifier = SegmentList(
                    segments = kwargs['subidentifier'] #TODO: copy?
                )
            else:
                self.subidentifier = SegmentList(str(kwargs['subidentifier']))
    
    def __lt__(self, other):
        return str(self) < str(other)
    def __le__(self, other):
        return str(self) <= str(other)
    def __eq__(self, other):
        return str(self) == str(other)
    def __ne__(self, other):
        return str(self) != str(other)
    def __gt__(self, other):
        return str(self) > str(other)
    def __ge__(self, other):
        return str(self) >= str(other)
    def __cmp__(self, other):
        return cmp(str(self), str(other))
    def __hash__(self):
        return hash(str(self))
    def __nonzero__(self):
        return bool(str(self))
    
    def __repr__(self):
        return "%s<%s>" % (self.__class__.__name__, self)
    def __unicode__(self):
        repr = str(self.identifier)
        if len(self.subidentifier) > 0:
            repr += "!" + str(self.subidentifier)
        return repr
    def __str__(self):
        return unicode(self).encode('utf-8')


class SegmentList(list):
    """
    Used for OsisPassage.identifier and OsisPassage.subidentifier; also could be used by OsisWork if we merely disallowed escapes.
    """
    
    def __init__(self, unparsed_input = "", **kwargs):
        self.remaining_input_unparsed = ""
        error_if_remainder = kwargs.get('error_if_remainder', True)
        
        if unparsed_input:
            segment_regex = re.compile(ur"""
                (?P<segment>   (?: \w | \\ \S )+ )
                (?P<delimiter>     \. | $     )?
            """, re.VERBOSE | re.UNICODE)
    
            self.remaining_input_unparsed = unparsed_input
            while len(self.remaining_input_unparsed) > 0:
                matches = segment_regex.match(self.remaining_input_unparsed)
                if not matches:
                    # Usually error if there is remaining that cannot be parsed
                    if error_if_remainder:
                        raise OsisError("Unxpected string at '%s' in '%s' for SegmentList" % (self.remaining_input_unparsed, unparsed_input))
                    # When OsisID invokes OsisWork, it will want to use the remaining
                    else:
                        break
                    
                segment = matches.group('segment')
                
                # Remove escapes
                segment = segment.replace("\\", "")
                self.append(segment)
                
                self.remaining_input_unparsed = self.remaining_input_unparsed[len(matches.group(0)):]
                
                # Handle case where no ending delimiter was found
                if matches.group("delimiter") is None:
                    if error_if_remainder:
                        raise OsisError("Expected ending delimiter at '%s' for SegmentList: %s" % (self.remaining_input_unparsed, unparsed_input))
                    else:
                        break
        
        # Allow members to be passed in discretely
        if kwargs.has_key('segments') and hasattr(kwargs['segments'], "__iter__"): #isinstance(kwargs['segments'], list):
            del self[:]
            self.extend(list(kwargs['segments']))
    
    def __repr__(self):
        return "%s<%s>" % (self.__class__.__name__, self)
    def __unicode__(self):
        return ".".join(
            map(
                lambda segment: re.sub(ur"(\W)", ur"\\\1", str(segment)),
                self
            )
        )
    def __str__(self):
        return unicode(self).encode('utf-8')


class OsisID():
    """
    An osisID which represents a passage within a single work like ESV:Exodus.1
    Includes a work prefix (OsisWork) and/or a passage (OsisPassage).
    
    Schema regexp:
    work: (((\p{L}|\p{N}|_)+)((\.(\p{L}|\p{N}|_)+)*)?:)?
    identifier: ((\p{L}|\p{N}|_|(\\[^\s]))+)((\.(\p{L}|\p{N}|_|(\\[^\s]))+)*)?
    subidentifier: (!((\p{L}|\p{N}|_|(\\[^\s]))+)((\.(\p{L}|\p{N}|_|(\\[^\s]))+)*)?)?
    
    >>> id = OsisID("Bible:John.1")
    >>> assert str(id) == "Bible:John.1"
    >>> assert str(id.work) == "Bible"
    >>> assert str(id.passage) == "John.1"
    >>> assert id.passage.identifier[0] == "John"
    
    >>> id = OsisID("John.3!a")
    >>> assert str(id.work) == ""
    >>> assert str(id.passage) == "John.3!a"
    >>> assert str(id.passage.subidentifier) == "a"
    
    >>> id = OsisID("Bible.en:")
    >>> assert str(id) == "Bible.en:"
    >>> assert str(id.work) == "Bible.en"
    
    >>> id = OsisID()
    >>> assert str(id) == ""
    >>> 
    >>> id = OsisID("Bible.KJV:",
    ...     passage = "John.3"
    ... )
    >>> assert str(id) == "Bible.KJV:John.3"
    >>> id.work = OsisWork()
    
    >>> id = OsisID("John.3.16",
    ...     work = "Bible.NIV"
    ... )
    >>> assert str(id) == "Bible.NIV:John.3.16"
    >>> 
    >>> id = OsisID(
    ...     work = OsisWork("Bible.NIV"),
    ...     passage = OsisPassage("John.3.16")
    ... )
    >>> assert str(id) == "Bible.NIV:John.3.16"
    >>> id.work = OsisWork("Bible.KJV")
    >>> assert str(id) == "Bible.KJV:John.3.16"
    """
    
    def __init__(self, unparsed_input = "", **kwargs):
        error_if_remainder = kwargs.get('error_if_remainder', True)
        
        if unparsed_input:
            self.remaining_input_unparsed = unparsed_input
            
            # Try to get the OsisWork component
            try:
                self.work = OsisWork(
                    unparsed_input,
                    error_if_remainder = False
                )
                if not self.work.remaining_input_unparsed.startswith(":"):
                    raise OsisError("Not starting with a work")
                self.remaining_input_unparsed = self.work.remaining_input_unparsed[1:]
            except:
                self.work = OsisWork()
            
            # Parse OsisPassage
            self.passage = OsisPassage(
                self.remaining_input_unparsed,
                error_if_remainder = False
            )
            self.remaining_input_unparsed = self.passage.remaining_input_unparsed
            
            if error_if_remainder and self.remaining_input_unparsed:
                raise OsisError("Remaining string not parsed at '%s' for OsisID: %s" % (self.remaining_input_unparsed, unparsed_input))
        
        else:
            self.work = OsisWork()
            self.passage = OsisPassage()
        
        # Allow members to be passed in discretely
        if kwargs.has_key('work'):
            if isinstance(kwargs['work'], OsisWork):
                self.work = kwargs['work'] #TODO: copy?
            else:
                self.work = OsisWork(str(kwargs['work']))
        if kwargs.has_key('passage'):
            if isinstance(kwargs['passage'], OsisPassage):
                self.passage = kwargs['passage'] #TODO: copy?
            else:
                self.passage = OsisPassage(str(kwargs['passage']))

    def __lt__(self, other):
        return str(self) < str(other)
    def __le__(self, other):
        return str(self) <= str(other)
    def __eq__(self, other):
        return str(self) == str(other)
    def __ne__(self, other):
        return str(self) != str(other)
    def __gt__(self, other):
        return str(self) > str(other)
    def __ge__(self, other):
        return str(self) >= str(other)
    def __cmp__(self, other):
        return cmp(str(self), str(other))
    def __hash__(self):
        return hash(str(self))
    def __nonzero__(self):
        return bool(str(self))
    
    def __repr__(self):
        return "%s<%s>" % (self.__class__.__name__, self)
    def __unicode__(self):
        work_str = str(self.work)
        passage_str = str(self.passage)
        
        if not work_str and not passage_str:
            return ""
        elif not work_str:
            return passage_str
        elif not passage_str:
            return work_str + ":"
        else:
            return work_str + ":" + passage_str
    def __str__(self):
        return unicode(self).encode('utf-8')





class OsisRef():
    """
    An osisRef which can contain a single passage from a work or a passage range from a work.
    Note: This should also allow for an arbitrary chain of references? Or just have a list?
    
    Schema regexp:
    (((\p{L}|\p{N}|_)+)((\.(\p{L}|\p{N}|_)+)*)?:)?
    ((\p{L}|\p{N}|_|(\\[^\s]))+)(\.(\p{L}|\p{N}|_|(\\[^\s]))*)*
    (!((\p{L}|\p{N}|_|(\\[^\s]))+)((\.(\p{L}|\p{N}|_|(\\[^\s]))+)*)?)?
    (@(cp\[(\p{Nd})*\]|s\[(\p{L}|\p{N})+\](\[(\p{N})+\])?))?
    (\-((((\p{L}|\p{N}|_|(\\[^\s]))+)(\.(\p{L}|\p{N}|_|(\\[^\s]))*)*)+)
    (!((\p{L}|\p{N}|_|(\\[^\s]))+)((\.(\p{L}|\p{N}|_|(\\[^\s]))+)*)?)?
    (@(cp\[(\p{Nd})*\]|s\[(\p{L}|\p{N})+\](\[(\p{N})+\])?))?)?
    
    >>> ref = OsisRef("Bible.KJV:John.2")
    >>> assert ref.work.type == "Bible"
    >>> assert ref.work.name == "KJV"
    >>> assert ref.start == ref.end
    >>> assert ref.start is not ref.end #due to deepcopy
    >>> assert ref.start.passage.identifier[0] == "John"
    >>> assert "Bible.KJV:John.2" == str(ref)
    >>> ref.end.passage.identifier[1] = "3" #John.3
    >>> assert "Bible.KJV:John.2-John.3" == str(ref)
    >>> ref.start.grain.type = "cp"
    >>> ref.start.grain.parameters.append(1)
    >>> assert str(ref.start) == "John.2@cp[1]"
    
    >>> ref2 = OsisRef(
    ...     work = "Bible.KJV",
    ...     start = "John.2@cp[1]",
    ...     end = "John.3"
    ... )   
    >>> assert ref == ref2
     
    >>> ref3 = OsisRef("Bible.KJV:",
    ...     start = OsisRef.Part(
    ...         passage = OsisPassage(
    ...             identifier = ["John", "2"]
    ...         ),
    ...         grain = OsisRef.Grain(
    ...             type = "cp",
    ...             parameters = [1]
    ...         )
    ...     ),
    ...     end = OsisRef.Part("John.3")
    ... )
    >>> assert ref2 == ref3
    
    >>> assert ref3.start != ref3.end
    >>> ref3.start.passage.identifier[1] = 3 #chapter
    >>> ref3.end.grain = OsisRef.Grain("cp[1]")
    >>> assert ref3.start == ref3.end
    
    >>> # In OsisRef, work is optional
    >>> ref = OsisRef("John.1-John.1")
    >>> assert "John.1" == str(ref) # collapses
    >>> ref.end.passage.identifier[1] = 2
    >>> assert "John.1-John.2" == str(ref) # uncollapses
    >>> ref.work = OsisWork("Bible.KJV")
    >>> assert "Bible.KJV:John.1-John.2" == str(ref)
    
    >>> # Try bad OsisRef
    >>> try:
    ...     ref = OsisRef("Bible.KJV:John.2.1!a:John.2.1!b  ")
    ...     raise Exception(True)
    ... except:
    ...     assert sys.exc_value is not True
    ... 
    >>> ref = OsisRef("Bible:John.1@cp[2]-John.2@cp[3]")
    >>> assert str(ref.work) == "Bible"
    >>> assert str(ref.start.passage) == "John.1"
    >>> assert str(ref.start.grain) == "cp[2]"
    >>> assert ref.start.grain.type == "cp"
    >>> assert ref.start.grain.parameters[0] == "2"
    """    
    
    def __init__(self, unparsed_input = "", **kwargs):
        error_if_remainder = kwargs.get('error_if_remainder', True)
        self.remaining_input_unparsed = unparsed_input
        
        if unparsed_input:
            
            # Try to get the OsisWork component
            try:
                self.work = OsisWork(
                    unparsed_input,
                    error_if_remainder = False
                )
                if not self.work.remaining_input_unparsed.startswith(":"):
                    raise OsisError("Not starting with a work")
                self.remaining_input_unparsed = self.work.remaining_input_unparsed[1:]
            except:
                self.work = OsisWork()
            
            # Parse start part
            self.start = OsisRef.Part(
                self.remaining_input_unparsed,
                error_if_remainder = False
            )
            self.remaining_input_unparsed = self.start.remaining_input_unparsed
            
            # Parse the end part
            if self.remaining_input_unparsed.startswith("-"):
                self.end = OsisRef.Part(
                    self.remaining_input_unparsed[1:],
                    error_if_remainder = False
                )
                self.remaining_input_unparsed = self.end.remaining_input_unparsed
            else:
                self.end = copy.deepcopy(self.start)
            
            if error_if_remainder and self.remaining_input_unparsed:
                raise OsisError("Remaining string not parsed at '%s' for OsisRef: %s" % (self.remaining_input_unparsed, unparsed_input))
        else:
            self.work = OsisWork()
            self.start = OsisRef.Part()
            self.end = OsisRef.Part()
        
        # Allow members to be passed in discretely
        if kwargs.has_key('work'):
            if isinstance(kwargs['work'], OsisWork):
                self.work = kwargs['work'] #TODO: copy?
            else:
                self.work = OsisWork(str(kwargs['work']))
        if kwargs.has_key('start'):
            if isinstance(kwargs['start'], OsisRef.Part):
                self.start = kwargs['start'] #TODO: copy?
            else:
                self.start = OsisRef.Part(str(kwargs['start']))
        if kwargs.has_key('end'):
            if isinstance(kwargs['end'], OsisRef.Part):
                self.end = kwargs['end'] #TODO: copy?
            else:
                self.end = OsisRef.Part(str(kwargs['end']))
    
    def __lt__(self, other):
        return str(self) < str(other)
    def __le__(self, other):
        return str(self) <= str(other)
    def __eq__(self, other):
        return str(self) == str(other)
    def __ne__(self, other):
        return str(self) != str(other)
    def __gt__(self, other):
        return str(self) > str(other)
    def __ge__(self, other):
        return str(self) >= str(other)
    def __cmp__(self, other):
        return cmp(str(self), str(other))
    def __hash__(self):
        return hash(str(self))
    def __nonzero__(self):
        return bool(str(self))
    
    def __unicode__(self):
        work_str = str(self.work)
        start_str = str(self.start)
        end_str = str(self.end)
        
        s = ""
        if work_str:
            s = work_str + ":"
        s += start_str
        if start_str != end_str:
            s += "-" + end_str
        return s
    def __str__(self):
        return unicode(self).encode('utf-8')
    
    
    class Part():
        """
        Represents the start or end points of an osisRef.
        
        Contains an OsisPassage and OsisRef.Grain
        
        >>> ref_part = OsisRef.Part("John.3.16@s[love]")
        >>> assert ref_part.passage.identifier[0] == "John"
        >>> assert ref_part.passage.identifier[1] == "3"
        >>> assert ref_part.passage.identifier[2] == "16"
        >>> assert str(ref_part.passage) == "John.3.16"
        
        >>> assert ref_part.grain.type == "s"
        >>> assert ref_part.grain.parameters[0] == "love"
        >>> assert str(ref_part.grain) == "s[love]"
        """
        
        def __init__(self, unparsed_input = "", **kwargs):
            error_if_remainder = kwargs.get('error_if_remainder', True)
            self.remaining_input_unparsed = ""
            
            if unparsed_input:
                # Parse OsisPassage
                self.passage = OsisPassage(
                    unparsed_input,
                    error_if_remainder = False
                )
                self.remaining_input_unparsed = self.passage.remaining_input_unparsed
                
                # Parse OsisRef.Grain
                if self.remaining_input_unparsed.startswith("@"):
                    self.grain = OsisRef.Grain(
                        self.remaining_input_unparsed[1:],
                        error_if_remainder = False
                    )
                    self.remaining_input_unparsed = self.grain.remaining_input_unparsed
                else:
                    self.grain = OsisRef.Grain()
                
                if error_if_remainder and self.remaining_input_unparsed:
                    raise OsisError("Remaining string not parsed at '%s' for OsisRef.Part: %s" % (self.remaining_input_unparsed, unparsed_input))
            
            else:
                self.passage = OsisPassage()
                self.grain = OsisRef.Grain()
            
            # Allow members to be passed in discretely
            if kwargs.has_key('passage'):
                if isinstance(kwargs['passage'], OsisPassage):
                    self.passage = kwargs['passage'] #TODO: copy?
                else:
                    self.passage = OsisPassage(str(kwargs['passage']))
            
            if kwargs.has_key('grain'):
                if isinstance(kwargs['grain'], OsisRef.Grain):
                    self.grain = kwargs['grain'] #TODO: copy?
                else:
                    self.grain = OsisRef.Grain(str(kwargs['grain']))
        
        def __lt__(self, other):
            return str(self) < str(other)
        def __le__(self, other):
            return str(self) <= str(other)
        def __eq__(self, other):
            return str(self) == str(other)
        def __ne__(self, other):
            return str(self) != str(other)
        def __gt__(self, other):
            return str(self) > str(other)
        def __ge__(self, other):
            return str(self) >= str(other)
        def __cmp__(self, other):
            return cmp(str(self), str(other))
        def __hash__(self):
            return hash(str(self))
        def __nonzero__(self):
            return bool(str(self))
            
        def __repr__(self):
            return "%s<%s>" % (self.__class__.__name__, self)
        def __unicode__(self):
            passage_str = str(self.passage)
            grain_str = str(self.grain)
            if grain_str:
                return passage_str + "@" + grain_str
            else:
                return passage_str
        def __str__(self):
            return unicode(self).encode('utf-8')
    
    # Should this be prefixed by '_'?
    class Grain():
        """
        Re-used by OsisRef for start and end OsisIDs
        
        OSIS Manual: “To refer to specific locations within a named canonical
        reference element, give the osisID as usual, followed by a "grain
        identifier", which consists of the character "@", and then an identifier for
        the portion desired.”
        
        Schema regexp: (@(cp\[(\p{Nd})*\]|s\[(\p{L}|\p{N})+\](\[(\p{N})+\])?))?
        
        >>> grain = OsisRef.Grain("cp[2]")
        >>> assert grain.type == "cp"
        >>> assert grain.parameters[0] == "2"
        >>> assert str(grain) == "cp[2]"
        """
        
        FORMATS = (
            # cp (code-point)
            re.compile(ur"(cp) \[(\d+)\]", re.U | re.X),
            # s (string)
            re.compile(ur"(s)  \[(\w+)\]  (?:\[(\d+)\])", re.U | re.X),
            # default
            re.compile(ur"(\w+)  (?:\[(.+?)\])+", re.U | re.X),
        )
        
        #class cp(self):
        #    regexp = re.compile(
        #        ur"cp\[(\d+)\]",
        #        re.UNICODE | re.VERBOSE
        #    )
        #    def _populate_params(self, match):
        #        self.parameters.append(match.group(1))
        #
        #class s(self):
        #    regexp = re.compile(
        #        ur"s\[(\w+)\](?:\[(\d+)\])",
        #        re.UNICODE | re.VERBOSE
        #    )
        #    def _populate_params(self, match):
        #        self.parameters.append(match.group(1), match.group(2))
        
        def __init__(self, unparsed_input = "", **kwargs):
            self.type = ""
            self.parameters = [] #TODO Use "params" instead?
            error_if_remainder = kwargs.get('error_if_remainder', True)
            self.remaining_input_unparsed = ""
            
            #if self.__class__ is OsisGrain:
            #    match = re.match(ur"(\w+)")
            #    if match and hasattr(self, match.group(1)):
            #        self = getattr(self, match.group(1))(unparsed_input, **kwargs)
            #    return
            
            # self.__class__ is OsisGrain
            
            
            if unparsed_input:
                
                for format in self.FORMATS:
                    match = re.match(format, unparsed_input)
                    if match:
                        break
                if not match:
                    raise OsisError("Unable to parse Grain: %s", unparsed_input)
                
                self.type = match.group(1)
                self.parameters.extend(match.groups()[1:])
                
                self.remaining_input_unparsed = self.remaining_input_unparsed[len(match.group(0)):]
                if error_if_remainder and self.remaining_input_unparsed:
                    raise OsisError("Remaining string not parsed at '%s' for Grain: %s" % (self.remaining_input_unparsed, unparsed_input))
            
            # Allow members to be passed in discretely
            if kwargs.has_key('type'):
                self.type = kwargs['type']
            if kwargs.has_key('parameters'):
                self.parameters = kwargs['parameters']
        
        def __lt__(self, other):
            return str(self) < str(other)
        def __le__(self, other):
            return str(self) <= str(other)
        def __eq__(self, other):
            return str(self) == str(other)
        def __ne__(self, other):
            return str(self) != str(other)
        def __gt__(self, other):
            return str(self) > str(other)
        def __ge__(self, other):
            return str(self) >= str(other)
        def __cmp__(self, other):
            return cmp(str(self), str(other))
        def __hash__(self):
            return hash(str(self))
        def __nonzero__(self):
            return bool(str(self))
        
        def __repr__(self):
            return "%s<%s>" % (self.__class__.__name__, self)
        def __unicode__(self):
            return self.type + "".join(
                map(
                    lambda param: '[' +  str(param) +  ']',
                    self.parameters
                )
            )
        def __str__(self):
            return unicode(self).encode('utf-8')


#### DEPRECATED!!! #####
def parse_osis_ref(osis_ref_string):
    """
    DEPRECATED. Use OsisRef object instead?
    """
    import sys
    sys.stderr.write("The parse_osis_ref function is deprecated in favor of the OsisRef object!")
    
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
        raise OsisError("Unable to parse osisRef")
    if not match.group('work_prefix') and not match.group('start_osis_id'):
        raise OsisError("Must have either work_prefix or osis_id")
    if not match.group('start_osis_id') and match.group('end_osis_id'):
        raise OsisError("If having an end osisID, you must have a start.")
    
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
                raise OsisError("Unexpected OSIS work prefix component: " + part)
        
        # Get the osis_slug and publisher
        if len(slugs) == 1:
            work_prefix['osis_slug'] = slugs[0]
        elif len(slugs) == 2:
            work_prefix['publisher'] = slugs[0]
            work_prefix['osis_slug'] = slugs[1]
        elif len(slugs) != 0:
            raise OsisError("Unexpected slug count in OSIS work prefix: " + str(work_prefix))
        
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
            raise OsisError("Invalid osisID: " + match.group('start_osis_id'))
        result['start_osis_id'] = id_match.groupdict()
        result['start_osis_id']['original'] = match.group('start_osis_id')
        
    # End osisID
    if match.group('end_osis_id'):
        id_match = parser.match(match.group('end_osis_id'))
        if not id_match:
            raise OsisError("Invalid osisID: " + match.group('end_osis_id'))
        result['end_osis_id'] = id_match.groupdict()
        result['end_osis_id']['original'] = match.group('end_osis_id')
    
    return result




# Tests
if __name__ == "__main__":
    import doctest
    doctest.testmod()

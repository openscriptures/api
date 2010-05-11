# coding: utf8 #
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
    REGEX = re.compile(ur"""
        \w+ (?: \. \w+ )*
        
        #( \w+ )(?: \. ( \w+ ))*
        #(?:
        #    (?:(?<!^) \. )?
        #    ( \w+ )
        #)+
    """, re.VERBOSE | re.UNICODE)
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
    
    def __init__(self, osis_work_str):
        self.type = None
        self.publisher = None
        self.name = None
        #self.date = None
        #self.year = None
        #self.month = None
        #self.day = None
        #self.time = None
        self.pub_date = None
        
        if __name__ == "__main__":
            print "OsisWork(%s)" % osis_work_str
        
        matches = self.REGEX.match(osis_work_str)
        #print "osis_work_str = ", osis_work_str
        #print matches.endpos-1 , len(osis_work_str)
        if not matches or len(matches.group(0)) != len(osis_work_str):
            raise Exception("Unable to parse string as a osisWork: %s" % osis_work_str)
        
        # Now that we've verified the pattern, now split it into segments
        # Is there a better way to tie this into the REGEX?
        segments = re.split(r"\.", osis_work_str)
        
        # Get the type
        if segments[0] in self.TYPES:
            self.type = segments.pop(0)
        
        # Get the language
        if len(segments) and re.match(r'^[a-z]{2,3}\b', segments[0]):
            self.language = segments.pop(0)
        
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
    

class OsisPassage():
    """
    OSIS passage such as Exodus.3.8 (i.e. without the work prefix)
    
    Organized into period-delimited segments increasingly narrowing in scope,
    followed by an optional sub-identifier which is work-specific.
    """
    REGEX = re.compile(ur"""
        ({segment})(?:\.({segment}))*
        
        # OSIS Manual: “Translations also often split verses into parts,
        # provided labels such as ‘a’ and ‘b’ for the separate parts. Encoders
        # may freely add sub-identifiers below the lowest standardized level.
        # They are set off from the standardized portion by the character ‘!’.”
        (?:!
            (?P<subidentifier>
                ({segment})(?:\.({segment}))*
            )
        )?
    """.format(
        segment=ur"((?:\w|\\\S)+)"
    ), re.VERBOSE | re.UNICODE)
    
    def __init__(self, osis_work_str):
        pass



class OsisID():
    """
    An osisID which represents a passage within a single work like ESV:Exodus.1
    Includes a work prefix (OsisWork) and/or a passage (OsisPassage).
    """
    REGEX = re.compile(
        ur"""
            #^
            (?:
                (?P<work>{work})
                :
            )?
            
            (?P<passage>{passage})?
            
            #$
        """.format(
            work = OsisWork.REGEX.pattern,
            passage = OsisPassage.REGEX.pattern
    ), re.VERBOSE | re.UNICODE)
    
    def __init__(self, osis_id_str):
        #osisIDRegExp = re.compile(OSIS_ID_REGEX, re.VERBOSE | re.UNICODE)
        
        self.work = None
        self.passage = None
        
        matches = self.REGEX.match(id)
        if not matches:
            raise Exception("Unable to parse osisID: " + osis_id_str)
        
        
        
        print matches.groups()
        print matches.groupdict()
        
        #assert(matches)


class OsisRef():
    """
    An osisRef which can contain a single passage from a work or a passage range from a work
    """
    #(@(cp\[(\p{Nd})*\]|s\[(\p{L}|\p{N})+\](\[(\p{N})+\])?))?
    start = None
    end = None
    
    
    #(((\p{L}|\p{N}|_)+)((\.(\p{L}|\p{N}|_)+)*)?:)?((\p{L}|\p{N}|_|(\\[^\s]))+)(\.(\p{L}|\p{N}|_|(\\[^\s]))*)*(!((\p{L}|\p{N}|_|(\\[^\s]))+)((\.(\p{L}|\p{N}|_|(\\[^\s]))+)*)?)?(@(cp\[(\p{Nd})*\]|s\[(\p{L}|\p{N})+\](\[(\p{N})+\])?))?(\-((((\p{L}|\p{N}|_|(\\[^\s]))+)(\.(\p{L}|\p{N}|_|(\\[^\s]))*)*)+)(!((\p{L}|\p{N}|_|(\\[^\s]))+)((\.(\p{L}|\p{N}|_|(\\[^\s]))+)*)?)?(@(cp\[(\p{Nd})*\]|s\[(\p{L}|\p{N})+\](\[(\p{N})+\])?))?)?
    
    def __init__(self, osis_ref_str):
        raise Exception("Not implemented")
    


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
    
    # Test OsisWork
    print "Testing OsisWork...";
    
    work = OsisWork("Bible")
    assert(work.type == "Bible")
    
    work = OsisWork("KJV")
    assert(work.type is None)
    assert(work.name == "KJV")
    
    work = OsisWork("Bible.en")
    assert(work.type == "Bible")
    assert(work.language == "en")
    
    work = OsisWork("Bible.en.KJV")
    assert(work.type == "Bible")
    assert(work.language == "en")
    assert(work.name == "KJV")
    
    work = OsisWork("Bible.en.KJV.1611")
    assert(work.language == "en")
    assert(work.name == "KJV")
    assert(work.pub_date.year == 1611)
    
    work = OsisWork("Bible.en.ChurchOfEngland.KJV.1611")
    assert(work.type == "Bible")
    assert(work.language == "en")
    assert(work.publisher == "ChurchOfEngland")
    assert(work.name == "KJV")
    assert(work.pub_date.year == 1611)
    
    work = OsisWork("KJV.1611.06.07")
    #work = OsisWork("KJV.1611-06-07")
    assert(work.name == "KJV")
    assert(work.pub_date.year == 1611)
    assert(work.pub_date.month == 6)
    assert(work.pub_date.day == 7)
    assert(work.pub_date.isoformat() == "1611-06-07T00:00:00")
    
    work = OsisWork("KJV.1611.06.07.235930")
    assert(work.pub_date.isoformat() == "1611-06-07T23:59:30")
    #assert(work.time.hour == 23)
    #assert(work.time.minute == 59)
    #assert(work.time.second == 30)
    #assert(work.time.microsecond == 0) # This is not implemented
    #assert(work.time.tzinfo is None) # Should this ever be anything else?
    
    
    
    
    exit()
    bad_works = [
        "@#$%^&",
        "Bible.Hello World Bible Society.NonExistantTranslation"
    ]
    for work in bad_works:
        try:
            obj = OsisWork(work)
            raise Exception(True)
        except:
            assert(sys.exc_value is not True)
    
    exit()
    
    # Test full osisID
    #osisIDRegExp = re.compile(OSIS_ID_REGEX, re.VERBOSE | re.UNICODE)
    ok_passages = [
        "John.1",
        "John.1.13",
        "John.A.13",
        "John.A.B.C.D",
        "John.A.B\.C\.D",
        "Bible:John.1",
        "Bible.KJV:John.1",
        "Bible.KJV.1611:John.1",
        "Bible.ChurchOfEngland.KJV.1611:John.1",
        
        "Esth.1.1!note.c",
        "Esth.1.1!crossReference"
    ]
    for passage in ok_passages:
        passage = OsisPassage(passage)
        
        #matches = osisIDRegExp.match(id)
        #assert(matches)
        #print id, matches.groups()
    
    # Test OsisID object
    
    
    # Test osisRef (extended)
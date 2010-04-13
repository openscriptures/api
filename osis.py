# coding: utf8 #
import re
from datetime import date

#((((\p{L}|\p{N}|_)+)(\.(\p{L}|\p{N}|_))*:)?([^:\s])+)
#OSIS_GEN_REGEX = ur"(((\w+)(?:\.(\w+))*:)?([^:\s])+)"
#OSIS_SCRIPTS = ur"([A-Z][a-z]{3}|x-[A-Za-z0-9]+)"


# (((\p{L}|\p{N}|_)+)((\.(\p{L}|\p{N}|_)+)*)?:)?
# ((\p{L}|\p{N}|_|(\\[^\s]))+)((\.(\p{L}|\p{N}|_|(\\[^\s]))+)*)?
# (!((\p{L}|\p{N}|_|(\\[^\s]))+)((\.(\p{L}|\p{N}|_|(\\[^\s]))+)*)?)?

OSIS_WORK_ID_REGEX = ur"\w+(?:\.\w+)*"
OSIS_SEGMENT_REGEX = ur"(?:\w|(?:\\[^\s]))+"

OSIS_ID_REGEX = ur"""
    ^
    (?:
        (?P<work>{work})
    :)?
    (?P<passage>
        ({segment})
        (?:\.({segment}))*
    )
    $
""".format(
    work = OSIS_WORK_ID_REGEX,
    segment = OSIS_SEGMENT_REGEX
)
    
#r"((\p{L}|\p{N}|_|(\\[^\s]))+)((\.(\p{L}|\p{N}|_|(\\[^\s]))+)*)?(!((\p{L}|\p{N}|_|(\\[^\s]))+)((\.(\p{L}|\p{N}|_|(\\[^\s]))+)*)?)?"
OSIS_REF_REGEX = ur"(((\p{L}|\p{N}|_)+)((\.(\p{L}|\p{N}|_)+)*)?:)?((\p{L}|\p{N}|_|(\\[^\s]))+)(\.(\p{L}|\p{N}|_|(\\[^\s]))*)*(!((\p{L}|\p{N}|_|(\\[^\s]))+)((\.(\p{L}|\p{N}|_|(\\[^\s]))+)*)?)?(@(cp\[(\p{Nd})*\]|s\[(\p{L}|\p{N})+\](\[(\p{N})+\])?))?(\-((((\p{L}|\p{N}|_|(\\[^\s]))+)(\.(\p{L}|\p{N}|_|(\\[^\s]))*)*)+)(!((\p{L}|\p{N}|_|(\\[^\s]))+)((\.(\p{L}|\p{N}|_|(\\[^\s]))+)*)?)?(@(cp\[(\p{Nd})*\]|s\[(\p{L}|\p{N})+\](\[(\p{N})+\])?))?)?"



#OSIS_WORK_PREFIX = ur"((//((\p{L}|\p{N}|_|-|\.|:)+))(/(\p{L}|\p{N}|_|-|\.|:)+)?(/@(\p{L}|\p{N}|_|-|\.|:)+))"

# ((\p{L}|\p{N}|_)+)((\.(\p{L}|\p{N}|_)+)*)?
OSIS_WORK_TYPE = ur"(\w+)(?:\.(\w+))*"

#L, N, Nd

#(\p{L}|\p{N}|_) = \w


#re.compile(r"\d", re.UNICODE) == /\p{N}/
#re.compile(r"\w", re.UNICODE) == /\p{N}|\p{L}|_/

TYPES = (
    "Bible",
    #"Quran",
    #"Mishnah",
    #"Talmud",
    #"BookOfMormon",
    # ...
)

#TODO: We need a way of creating/storing arbitrary canonical book orders
#TODO: Include facility for converting natural language references into osisRefs?

#BIBLE_BOOK_CODES = (
#    "Gen", "Exod", "Lev", "Num", "Deut", "Josh", "Judg", "Ruth", "1Sam", "2Sam", "1Kgs", "2Kgs", "1Chr", "2Chr", "Ezra", "Neh", "Esth", "Job", "Ps", "Prov", "Eccl", "Song", "Isa", "Jer", "Lam", "Ezek", "Dan", "Hos", "Joel", "Amos", "Obad", "Jonah", "Mic", "Nah", "Hab", "Zeph", "Hag", "Zech", "Mal",
#    "Matt", "Mark", "Luke", "John", "Acts", "Rom", "1Cor", "2Cor", "Gal", "Eph", "Phil", "Col", "1Thess", "2Thess", "1Tim", "2Tim", "Titus", "Phlm", "Heb", "Jas", "1Pet", "2Pet", "1John", "2John", "3John", "Jude", "Rev",
#    "Bar", "AddDan", "PrAzar", "Bel", "SgThree", "Sus", "1Esd", "2Esd", "AddEsth", "EpJer", "Jdt", "1Macc", "2Macc", "3Macc", "4Macc", "PrMan", "Sir", "Tob", "Wis"
#)

BOOK_ORDERS = {
    "Bible": {
        "KJV": [
            "Gen", "Exod", "Lev", "Num", "Deut", "Josh", "Judg", "Ruth", "1Sam", "2Sam", "1Kgs", "2Kgs", "1Chr", "2Chr", "Ezra", "Neh", "Esth", "Job", "Ps", "Prov", "Eccl", "Song", "Isa", "Jer", "Lam", "Ezek", "Dan", "Hos", "Joel", "Amos", "Obad", "Jonah", "Mic", "Nah", "Hab", "Zeph", "Hag", "Zech", "Mal",
            "Matt", "Mark", "Luke", "John", "Acts", "Rom", "1Cor", "2Cor", "Gal", "Eph", "Phil", "Col", "1Thess", "2Thess", "1Tim", "2Tim", "Titus", "Phlm", "Heb", "Jas", "1Pet", "2Pet", "1John", "2John", "3John", "Jude", "Rev",
            "Bar", "AddDan", "PrAzar", "Bel", "SgThree", "Sus", "1Esd", "2Esd", "AddEsth", "EpJer", "Jdt", "1Macc", "2Macc", "3Macc", "4Macc", "PrMan", "Sir", "Tob", "Wis"
        ]
    }
}

#PROBLEM: Osis Book Names are biased toward the KJV tradition
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


class OsisID():
    #(((\p{L}|\p{N}|_)+)((\.(\p{L}|\p{N}|_)+)*)?:)?((\p{L}|\p{N}|_|(\\[^\s]))+)((\.(\p{L}|\p{N}|_|(\\[^\s]))+)*)?(!((\p{L}|\p{N}|_|(\\[^\s]))+)((\.(\p{L}|\p{N}|_|(\\[^\s]))+)*)?)?
    
    
    #(((\p{L}|\p{N}|_)+)((\.(\p{L}|\p{N}|_)+)*)?:)?
    #((\p{L}|\p{N}|_|(\\[^\s]))+)((\.(\p{L}|\p{N}|_|(\\[^\s]))+)*)?
    #(!((\p{L}|\p{N}|_|(\\[^\s]))+)((\.(\p{L}|\p{N}|_|(\\[^\s]))+)*)?)?
    pass

class OsisRef():
    """
    An osisRef which can contain a single passage from a work or a passage range from a work
    """
    
    start = None
    end = None
    
    
    #(((\p{L}|\p{N}|_)+)((\.(\p{L}|\p{N}|_)+)*)?:)?((\p{L}|\p{N}|_|(\\[^\s]))+)(\.(\p{L}|\p{N}|_|(\\[^\s]))*)*(!((\p{L}|\p{N}|_|(\\[^\s]))+)((\.(\p{L}|\p{N}|_|(\\[^\s]))+)*)?)?(@(cp\[(\p{Nd})*\]|s\[(\p{L}|\p{N})+\](\[(\p{N})+\])?))?(\-((((\p{L}|\p{N}|_|(\\[^\s]))+)(\.(\p{L}|\p{N}|_|(\\[^\s]))*)*)+)(!((\p{L}|\p{N}|_|(\\[^\s]))+)((\.(\p{L}|\p{N}|_|(\\[^\s]))+)*)?)?(@(cp\[(\p{Nd})*\]|s\[(\p{L}|\p{N})+\](\[(\p{N})+\])?))?)?
    
    def __init__(self):
        raise Exception("Not implemented")
    



def parse_osis_ref(osis_ref_string):
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
    
    # Test workID
    workIDRegExp = re.compile(OSIS_WORK_ID_REGEX, re.VERBOSE | re.UNICODE)
    ok_workIDs = [
        "Bible",
        "Bible.KJV",
        "Bible.KJV.1611",
        "Bible.ChurchOfEngland.KJV.1611"
    ]
    for id in ok_workIDs:
        matches = workIDRegExp.match(id)
        assert(matches)
        #print id, matches.groups()
    
    # Test full osisID
    osisIDRegExp = re.compile(OSIS_ID_REGEX, re.VERBOSE | re.UNICODE)
    ok_osisIDs = [
        "John.1",
        "John.1.13",
        "John.A.13",
        "John.A.B.C.D",
        "John.A.B\.C\.D",
        "Bible:John.1",
        "Bible.KJV:John.1",
        "Bible.KJV.1611:John.1",
        "Bible.ChurchOfEngland.KJV.1611:John.1"
    ]
    for id in ok_osisIDs:
        matches = osisIDRegExp.match(id)
        assert(matches)
        #print id, matches.groups()
    
    # Test osisRef (extended)
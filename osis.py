# coding: utf8 #
import re

BIBLE_BOOK_CODES = (
    "Gen", "Exod", "Lev", "Num", "Deut", "Josh", "Judg", "Ruth", "1Sam", "2Sam", "1Kgs", "2Kgs", "1Chr", "2Chr", "Ezra", "Neh", "Esth", "Job", "Ps", "Prov", "Eccl", "Song", "Isa", "Jer", "Lam", "Ezek", "Dan", "Hos", "Joel", "Amos", "Obad", "Jonah", "Mic", "Nah", "Hab", "Zeph", "Hag", "Zech", "Mal",
    "Matt", "Mark", "Luke", "John", "Acts", "Rom", "1Cor", "2Cor", "Gal", "Eph", "Phil", "Col", "1Thess", "2Thess", "1Tim", "2Tim", "Titus", "Phlm", "Heb", "Jas", "1Pet", "2Pet", "1John", "2John", "3John", "Jude", "Rev",
    "Bar", "AddDan", "PrAzar", "Bel", "SgThree", "Sus", "1Esd", "2Esd", "AddEsth", "EpJer", "Jdt", "1Macc", "2Macc", "3Macc", "4Macc", "PrMan", "Sir", "Tob", "Wis"
)

BIBLE_BOOK_NAMES = {
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


def parse_osis_ref(osis_ref_string):
    parser = re.compile(ur"""
        ^(?:
            (?P<osis_work>.+?
                #(?P<type>\w+)
                #(?:\.(?P<language>[a-z]\w*))?
                #(?:\.(?P<slug1>\w+))?
                #(?:\.(?P<slug2>\w+))?
                #(?:\.(?P<publish_date>.+))?
            ):
        )?
        (?P<start_osis_id>
            .+?
        )
        (?:-
            (?P<end_osis_id>
               .+? 
            )
        )?$
    """, re.VERBOSE)
    match = parser.match(osis_ref_string)
    if not match:
        raise Exception("Unable to parse osisRef")
    group = match.groupdict()
    print group['osis_work'].split('.')
    
    
    
    if group.has_key('slug2'):
        group['publisher'] = group['slug1']
        group['osis_slug'] = group['slug2']
        del group['slug1']
        del group['slug2']
    elif group.has_key('slug1'):
        group['publisher'] = None
        group['osis_slug'] = group['slug1']
        del group['slug1']
    
    return group
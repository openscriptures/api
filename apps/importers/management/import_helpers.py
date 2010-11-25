#!/usr/bin/env python
# encoding: utf-8

import os
import sys
import urllib
import unicodedata
import base64
import hashlib
from django.utils.encoding import smart_str

from texts.models import Work, Token
from core import osis

def generate_token_id(work_id, passage_id, previous_tokens, token_data):
    hash = base64.b32encode(hashlib.sha256(
        "".join((
            smart_str(work_id),
            smart_str(passage_id),
            "".join(
                [smart_str(token.data) for token in previous_tokens[-3:]]
            ),
            smart_str(token_data)
        ))
    ).digest())
    
    hash = hash.strip('=')
    assert(len(hash) == 52)
    return hash

def normalize_token(data):
    "Normalize to Unicode NFC, strip out all diacritics, apostrophies, and make lower-case."
    # credit: http://stackoverflow.com/questions/517923/what-is-the-best-way-to-remove-accents-in-a-python-unicode-string
    data = unicodedata.normalize('NFC', ''.join((c for c in unicodedata.normalize('NFD', data) if unicodedata.category(c) != 'Mn')).lower())
    data = data.replace(r'\s+', ' ')
    #data = re.sub(ur"['’]", '', data)
    data = data.replace(u"'", '')
    data = data.replace(u"’", '')
    return data


def download_resource(source_url):
    "Download the file in the provided URL if it does not already exist in the working directory."
    if(not os.path.exists(os.path.basename(source_url))):
        if(not os.path.exists(os.path.basename(source_url))):
            print "Downloading " + source_url
            urllib.urlretrieve(source_url, os.path.basename(source_url))


def abort_if_imported(workID, force=False):
    "Shortcut see if the provided work ID already exists in the system; if so, then abort unless --force command line argument is supplied"
    if(len(Work.objects.filter(id=workID)) and not force):
        print " (already imported; pass --force option to delete existing work and reimport)"
        exit()


def delete_work(workID):
    "Deletes a work without a greedy cascade"
    
    try:
        work = Work.objects.get(id = workID)
    except:
        return False

    #if work.variants_for_work is not None:
    #    delete_work(work.variants_for_work.id)
    
    # Clear all links to unified text
    Token.objects.filter(work = workID).delete() #Does this need to be two linces?
    
    # Delete all variant works
    #Work.objects.filter(variants_for_work = workID).delete()
    
    # Delete work
    #Work.objects.filter(id=workID).update(unified_token=None)
    Work.objects.filter(id=workID).delete()
    return True


def get_book_code_args():
    book_codes = []
    for arg in sys.argv:
        if arg in osis.BIBLE_BOOK_CODES:
            book_codes.append(arg)
    return book_codes

def close_structure(element, bookTokens, structs):
    if structs.has_key(element):
        assert(structs[element].start_token is not None)
        if structs[element].end_token is None:
            structs[element].end_token = bookTokens[-1]
        structs[element].save()
        del structs[element]


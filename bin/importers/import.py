import re, os, sys

importScripts = (
    #'greek_WH_UBS4_parsed.py',
    'Tischendorf-2.5.py',
    #'greek_byzantine_2000_parsed.py',
    #'greek_byzantine_2005_parsed.py',
    #'greek_textus_receptus_parsed.py',
    #'TNT.py',
)
for script in importScripts:
    print "## %s ##" % script
    #execfile(script)
    os.system('python ' + script + ' ' + ''.join(sys.argv[1:]))

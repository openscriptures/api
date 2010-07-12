# -*- coding: utf-8 -*-

import sys, os
sys.path.append(os.path.abspath(os.curdir))
sys.path.append(os.path.abspath(os.pardir))
os.environ["DJANGO_SETTINGS_MODULE"] = "settings"

VERSION = __import__('texts').__version__

extensions = ['sphinx.ext.autodoc']
templates_path = ['_templates']
source_suffix = '.txt'
master_doc = 'index'

project = u'OpenScriptures Texts'
copyright = u'2010, Weston Ruter'
version = VERSION
release = VERSION

exclude_patterns = ['_build']
pygments_style = 'sphinx'
html_theme = 'default'
html_static_path = ['_static']
html_last_updated_fmt = '%b %d, %Y'
htmlhelp_basename = 'texts-docs'

latex_documents = [
  ('index', 'texts.tex', u'texts Documentation', u'Weston Ruter', 'manual'),
]

man_pages = [
    ('index', 'texts', u'texts Documentation',  [u'Weston Ruter'], 1)
]

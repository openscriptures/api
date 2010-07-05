# coding: utf8 #

from django.db import models
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _


class Language(models.Model):
    """
    A human language, either ancient or modern.
    """

    DIRECTIONS = (
        ('ltr', 'Left to Right'),
        ('rtl', 'Right to Left'),
        #also needing vertical directions, see CSS writing-mode
    )

    code = models.CharField(_("ISO 639-3 language code"), max_length=10, primary_key=True)
    name = models.CharField(max_length=32)
    direction = models.CharField(_("Text directionality"), max_length=3, choices=DIRECTIONS, default='ltr')
    
    def __unicode__(self):
        return self.name


class License(models.Model):
    """
    A license that a work uses to indicate the copyright restrictions or
    permissions.
    """

    name = models.CharField(max_length=128)
    abbreviation = models.CharField(max_length=32, blank=True, db_index=True)
    url = models.URLField(_("Primary URL which defines the license."), blank=True)

    # We need a matrix describing what the license allows:
    # - attribution
    # - noncommercial
    # - share_alike
    # - no_derivatives
    isolatable = models.BooleanField(_("If this is true, then this work can be displayed independently. Otherwise, it must only be displayed in conjunction with other works. Important condition for fair use license."), default=True)

    def __unicode__(self):
        return self.name


class Server(models.Model):
    """
    A server that hosts the Open Scriptures API
    """

    is_self = models.BooleanField(_("Whether the server refers to itself"))
    base_url = models.URLField(_("The base URL that the API URIs can be appended to."))
    #version = models.CharField(max_length=5, default="1")
    #Idea: adapters for URL rewriting and response transformation so that servers need not be compatible with Open Scriptures API

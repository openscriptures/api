from django.db import models
from openscriptures_api_texts import Token
from openscriptures_api import Language

class TokenMeta(models.Model):
    """
    Metadata about each token, including language, parsing information, etc.
    """

    token = models.ForeignKey(Token, related_name="token_parsing_set")
    work = models.ForeignKey(Work, null=True, blank=True, help_text=_("The work that defines this parsing; may be null since a user may provide it. Usually same as token.work"))
    language = models.ForeignKey(Language, null=True, blank=True, help_text=_("The language of the token. Not necessarily the same as token.work.language"))
    # TODO: Should be changed to a ForeignKey linking to strongs db when that comes online
    strongs = models.CharField(max_length=255, help_text=_("The strongs number, prefixed by 'H' or 'G' specifying whether it is for the Hebrew or Greek, respectively. Multiple numbers separated by semicolon."))
    # TODO: Lemma should probably expressed in TokenParsing_* objects,
    #       since there can be a difference of opinion in some cases.
    lemma = models.CharField(max_length=255, help_text=_("The lemma chosen for this token. Need not be supplied if strongs given. If multiple lemmas are provided, then separate with semicolon."))

    # TODO: Get these TokenParsing models established
    def get_parsing(self):
        if self.language.code == "grc":
            return TokenParsing_grc.objects.get(tokenmeta = self)
        elif self.language.code == "hbo":
            return TokenParsing_hbo.objects.get(tokenmata = self)
        else:
            raise Exception(_("Unknown parsing language."))

    parsing = property(get_parsing)


class TokenParsing_grc(models.Model):
    """
    Represent Greek parsing information for a given Token.
    """

    tokenmeta = models.ForeignKey(TokenMeta)
    # Choicse here
    # From Smyth's grammar
    PARTS_OF_SPEECH = (
        ('Noun', _('Noun')),
        ('Adjective', _('Adjective')),
        ('Pronoun', _('Pronoun')),
        ('Verb', _('Verb')),
        ('Adverb', _('Adverb')),
        ('Preposition', _('Preposition')),
        ('Conjunction', _('Conjunction')),
        ('Particle', _('Particle')),
    )

    NUMBERS = (
        ('Singular', _('Singular')),
        ('Dual', _('Dual')),
        ('Plural', _('Plural')),
    )

    GENDERS = (
        ('Masculine', _('Masculine')),
        ('Feminine', _('Feminine')),
        ('Neuter', _('Neuter')),
    )

    CASES = (
        ('Nominative', _('Nominative')),
        ('Genitive', _('Genitive')),
        ('Dative', _('Dative')),
        ('Accusative', _('Accusative')),
        ('Vocative', _('Vocative')),
    )

    # TODO: Should 2nd aorist be expressed here, or have its own field?
    TENSES = (
        ('Present', _('Present')),
        ('Imperfect', _('Imperfect')),
        ('Future', _('Future')),
        ('Aorist', _('Aorist')),
        ('Perfect', _('Perfect')),
        ('Pluperfect', _('Pluperfect')),
        ('Future Perfect', _('Future Perfect')),
    )

    VOICES = (
        ('Active', _('Active')),
        ('Middle', _('Middle')),
        ('Passive', _('Passive')),
    )

    MOODS = (
        ('Indicative', _('Indicative')),
        ('Subjunctive', _('Subjunctive')),
        ('Optative', _('Optative')),
        ('Imperative', _('Imperative')),
        ('Infinitive', _('Infinitive')),
        ('Participle', _('Participle')),
    )

    PERSONS = (
        ('First', _('First')),
        ('Second', _('Second')),
        ('Third', _('Third')),
    )

    # Fields here
    part = models.CharField(max_length=12, choices=PARTS_OF_SPEECH)
    substantival_number = models.CharField(max_length=12, choices=NUMBERS, blank=True)
    gender = models.CharField(max_length=12, choices=GENDERS, blank=True)
    case = models.CharField(max_length=12, choices=CASES, blank=True)
    tense = models.CharField(max_length=20, choices=TENSES, blank=True)
    voice = models.CharField(max_length=12, choices=VOICES, blank=True)
    mood = models.CharField(max_length=20, choices=MOODS, blank=True)
    person = models.CharField(max_length=12, choices=PERSONS, blank=True)
    verbal_number = models.CharField(max_length=12, choices=NUMBERS, blank=True)
    # TODO: Model validation for parsings based on part of speech, mood, etc.


class TokenParsing_hbo(models.Model):
    """
    Represent Hebrew parsing information for a given Token.
    """

    tokenmeta = models.ForeignKey(TokenMeta)
    # TODO: Create the rest of the parsing model


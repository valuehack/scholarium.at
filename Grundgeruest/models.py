"""
Die Modelle für Projektweite Daten: Menüpunkte, Nutzer/Profile

 - eingegeben wird eine slug (absolut, bezüglich /) und eine nummer, die die
   Reihenfolge im Menü bestimmt
 - was wird an das Template übergeben? Vielleicht lieber eine Liste für jede
   Nutzerkategorie erstellen? Dann fällt nummer weg.
"""

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.utils.translation import ugettext as _
from userena.models import UserenaBaseProfile, UserenaSignup
from userena.utils import generate_sha1
from django.core.validators import RegexValidator
import random
from django_countries.fields import CountryField
from datetime import datetime

from seite.models import Grundklasse

class Menuepunkt(Grundklasse):
    sichtbar_ab = models.IntegerField(
        blank=True,
        default=0)
    nummer = models.IntegerField(default=1)

    class Meta:
        abstract = True
        ordering = ['nummer']

class GanzesMenue(Grundklasse):
    pass

class Hauptpunkt(Menuepunkt):
    gehoert_zu = models.ForeignKey(GanzesMenue)
    class Meta: verbose_name_plural = 'Menü - Hauptpunkte'

class Unterpunkt(Menuepunkt):
    gehoert_zu = models.ForeignKey(Hauptpunkt)
    class Meta: verbose_name_plural = 'Menü - Unterpunkte'
    def __str__(self):
        return "{}: {} - {}".format(
            self.gehoert_zu.gehoert_zu.bezeichnung,
            self.gehoert_zu.bezeichnung,
            self.bezeichnung)

class Nutzer(AbstractUser):
    @staticmethod
    def erzeuge_zufall(laenge, sonderzeichen=3):
        s = ['abcdefghijkmnopqrstuvwxyz',
            'ABCDEFGHJKLMNPQRSTUVWXYZ',
            '23456789_-',
            '@.%&+!$?/()#*']
        zufall = []
        for i in range(laenge):
            zufall.append(random.sample(s[i % sonderzeichen], 1)[0])
        return ''.join(zufall)

    @staticmethod
    def erzeuge_pw():
        return Nutzer.erzeuge_zufall(7, sonderzeichen=4)

    @staticmethod
    def erzeuge_username():
        return Nutzer.erzeuge_zufall(12)

    def hat_guthaben(self):
        return bool(self.my_profile.guthaben)

    @classmethod
    def leeren_anlegen(cls):
        username = cls.erzeuge_username()

        nutzer = UserenaSignup.objects.create_user(username,
                                                     email='spam@spam.de',
                                                     password='spam',
                                                     active=False,
                                                     send_email=False)

        signup = nutzer.userena_signup
        salt, hash = generate_sha1(nutzer.username)
        signup.activation_key = hash
        signup.save()

        return nutzer

    def versende_activation(self):
        """ Autogeneriere pw und versende activation mail incl. pw """
        # activation Mail mit pw versenden
        from userena.mail import UserenaConfirmationMail
        import userena.settings as userena_settings
        from django.contrib.sites.models import Site
        from userena.utils import get_protocol

        signup = self.userena_signup
        password = self.erzeuge_pw()

        context = {'user': signup.user,
                  'without_usernames': userena_settings.USERENA_WITHOUT_USERNAMES,
                  'protocol': get_protocol(),
                  'activation_days': userena_settings.USERENA_ACTIVATION_DAYS,
                  'activation_key': signup.activation_key,
                  'site': Site.objects.get_current(),
                  'passwort': password}

        mailer = UserenaConfirmationMail(context=context)
        mailer.generate_mail("activation")
        mailer.send_mail(signup.user.email)

        self.set_password(password)
        self.save()

    @classmethod
    def neuen_erstellen(cls, email):
        """ Erstellt neuen Nutzer mit angegebener Mailadresse

        Es wird die Methode von UserenaSignup verwendet, sodass gleich-
        zeitig ein signup-Objekt für den Nutzer sowie alle UserObjectPer-
        missions erzeugt werden.
        Ich erstelle auch gleich ein Profil dazu, zur Vollständigkeit.
        Es wird ein Passwort per Zufall gesetzt und an die confirmation
        mail übergeben.
        """
        nutzer = Nutzer.leeren_anlegen()
        nutzer.email = email
        nutzer.save()
        nutzer.versende_activation()
        return nutzer

    def save(self, *args, **kwargs):
        if not self.username:
            self.username = self.erzeuge_zufall(16)
        super(Nutzer, self).save(*args, **kwargs)

    def __str__(self):
        return 'Nutzer {}'.format(self.email)

class ScholariumProfile(UserenaBaseProfile):
    user = models.OneToOneField(settings.AUTH_USER_MODEL,
                                unique=True,
                                verbose_name=_('user'),
                                related_name='my_profile')
    stufe_choices = [(0, 'Interessent'),
        (1, 'Gast'),
        (2, 'Teilnehmer'),
        (3, 'Scholar'),
        (4, 'Partner'),
        (5, 'Beirat'),
        (6, 'Patron')]
    stufe = models.IntegerField(
        choices=stufe_choices,
        default=0)
    anrede = models.CharField(
        max_length=4,
        choices=[('Herr', 'Herr'), ('Frau', 'Frau')],
        default='Herr', null=True)
    tel = models.CharField(
        max_length=20,
        null=True, blank=True)
    firma = models.CharField(
        max_length=30,
        null=True, blank=True)
    strasse = models.CharField(
        max_length=30,
        null=True, blank=True)
    plz = models.CharField(
        max_length = 5,
        validators=[RegexValidator('^[0-9]+$')],
        null=True, blank=True)
    ort = models.CharField(
        max_length=30,
        null=True, blank=True)
    land = CountryField(
        blank_label='- Bitte Ihr Land auswählen -',
        null=True)
    guthaben = models.SmallIntegerField(default=0)
    titel = models.CharField(
        max_length=30,
        null=True, blank=True)
    anredename = models.CharField(
        max_length=30,
        null=True, blank=True)
    letzte_zahlung = models.DateField(null=True, blank=True)
    datum_ablauf = models.DateField(null=True, blank=True)
    alt_id = models.SmallIntegerField(
        default=0, editable=False)
    alt_notiz = models.CharField(
        max_length=255, null=True,
        default='', editable=False)
    alt_scholien = models.SmallIntegerField(
        default=0, null=True, editable=False)
    alt_mahnstufe = models.SmallIntegerField(
        default=0, null=True, editable=False)
    alt_auslaufend = models.SmallIntegerField(
        default=0, null=True, editable=False)
    alt_gave_credits = models.SmallIntegerField(
        default=0, null=True, editable=False)
    alt_registration_ip = models.GenericIPAddressField(
        editable=False, null=True)

    def get_Status(self):
        status = [
            (0, "Kein Unterstützer"),
            (1, "Abgelaufen"),
            (2, "30 Tage bis Ablauf"),
            (3, "Aktiv")
        ]
        if self.datum_ablauf == None:
            return status[0]
        else:
            verbleibend = (self.datum_ablauf - datetime.now().date()).days
            if self.stufe == 0:
                return status[0]
            elif verbleibend < 0:
                return status[1]
            elif verbleibend < 30:
                return status[2]
            else:
                return status[3]

    def guthaben_aufladen(self, betrag):
        """ wird spaeter nuetzlich, wenn hier mehr als die eine Zeile^^ """
        self.guthaben += int(betrag)

    class Meta():
        verbose_name = 'Nutzerprofil'
        verbose_name_plural = 'Nutzerprofile'

class Mitwirkende(models.Model):

    level_choices = [(1, 'Rektor'),
        (2, 'Gründer'),
        (3, 'Mitarbeiter'),
        (4, 'Mentor'),
        (8, 'Student')]

    name = models.CharField(max_length=100)
    alt_id = models.PositiveSmallIntegerField(default=0)
    text_de = models.TextField(null=True, blank=True)
    text_en = models.TextField(null=True, blank=True)
    link = models.URLField(null=True, blank=True)
    level = models.PositiveSmallIntegerField(default=1,
        choices=level_choices)
    start = models.DateField(null=True, blank=True)
    end = models.DateField(null=True, blank=True)

    class Meta:
        verbose_name = "Mitwirkender"
        verbose_name_plural = "Mitwirkende"
        ordering = ('level', 'start', 'alt_id')

    def __str__(self):
        return self.name

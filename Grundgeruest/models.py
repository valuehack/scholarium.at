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
from django.core.validators import RegexValidator
import random

#from Produkte.models import Produkt
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
    
    def save(self, *args, **kwargs):
        if not self.username:
            self.username = self.erzeuge_zufall(16)
        super(Nutzer, self).save(*args, **kwargs)

class MeinUserenaSignup(UserenaSignup):
    def send_activation_email(self, **kwargs):
        """
        Ich aendere die Funktion ab.
        Damit Context auch dass Passwort enthaelt
        """
        from userena.mail import UserenaConfirmationMail
        import userena.settings as userena_settings
        from django.contrib.sites.models import Site
        from userena.utils import get_protocol

        context = {'user': self.user,
                  'without_usernames': userena_settings.USERENA_WITHOUT_USERNAMES,
                  'protocol': get_protocol(),
                  'activation_days': userena_settings.USERENA_ACTIVATION_DAYS,
                  'activation_key': self.activation_key,
                  'site': Site.objects.get_current(),
                  'passwort': kwargs['pw']}
        
        mailer = UserenaConfirmationMail(context=context)
        mailer.generate_mail("activation")
        mailer.send_mail(self.user.email)


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
    land = models.CharField(
        max_length=30,
        null=True, blank=True)    
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

    def darf_scholien_sehen(self):
        if self.guthaben < 20:
            return True
        else:
            raise TypeError('Guthaben zu hoch, editiere ScholariumProfile.darf_scholien_sehen()')
    
    def guthaben_aufladen(self, betrag):
        """ wird spaeter nuetzlich, wenn hier mehr als die eine Zeile^^ """
        self.guthaben += int(betrag)
        
    class Meta():
        verbose_name = 'Nutzerprofil'
        verbose_name_plural = 'Nutzerprofile'

class Mitwirkende(models.Model):
    name = models.CharField(max_length=100)
    text_de = models.TextField(null=True, blank=True)
    text_en = models.TextField(null=True, blank=True)
    link = models.CharField(max_length=200, null=True, blank=True)
    level = models.CharField(max_length=30)
    start = models.DateField(null=True, blank=True)
    end = models.DateField(null=True, blank=True)
    class Meta:
        verbose_name = "Mitwirkender"
        verbose_name_plural = "Mitwirkende"
    
    def __str__(self):
        return self.name

    #def gegenwerte_html(self):
    #    gegenwerte = []
    #    for i in range(1, 7):
    #        if getattr(self, 'gegenwert%s' % i):
    #            gegenwerte.append(getattr(self, 'gegenwert%s' % i))
    #    return gegenwerte

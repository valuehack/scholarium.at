"""
Die Modelle der Veranstaltungen und Medien
 - die ArtDerVeranstaltung speichert gemeinsame Attribute
 - eine Veranstaltung muss einer Art zugeordnet sein (zu überdenken?)
 - ein Medium kann gehoert_zu Veranstaltung sein und erbt div. Attribute
 - kann auch selbst Preis, Datum, etc, festlegen
 - beim 1.Speichern von Veranstaltung oder Medium wird neues Produkt erstellt
"""

from django.db import models
from seite.models import Grundklasse
from Produkte.models import KlasseMitProdukten
from django.core.urlresolvers import reverse
from datetime import date
import random, string


class Veranstaltung(KlasseMitProdukten):
    beschreibung = models.TextField()
    beschreibung2 = models.TextField(null=True, blank=True)
    datum = models.DateField()
    art_veranstaltung = models.ForeignKey('ArtDerVeranstaltung')
    datei = models.FileField(null=True, blank=True) # für Aufzeichnung
    link = models.URLField(null=True, blank=True) # youtube-link
    ob_chat_anzeigen = models.BooleanField(default=False)
    arten_liste = ['teilnahme', 'livestream', 'aufzeichnung']

    @property
    def livestream(self):
        return self.link
    @property
    def aufzeichnung(self):
        return self.datei

    class Meta:
        verbose_name_plural = "Veranstaltungen"
        verbose_name = "Veranstaltung"

    def get_absolute_url(self):
        art = self.art_veranstaltung.bezeichnung.lower()
        prefix = 'vortrag' if art=='vorlesung' else art
        return "/%s/%s/" % (prefix, self.slug)

    def preis_ausgeben(self, art='teilnahme'):
        """ Preis ausgeben, es gibt nur eine art für Präsenz? oder Medium-model hier einfügen, dann mehr? """
        if art not in self.arten_liste:
            raise ValueError('Bitte gültige Art angeben')
        elif self.finde_preis(art):
            return self.finde_preis(art)
        else: # kein individueller Preis, gucke nach Art
            return getattr(self.art_veranstaltung, 'preis_'+art)

    def ob_aktiv(self, art='teilnahme'):
        if art not in self.arten_liste:
            raise ValueError('Bitte gültige Art angeben')
        elif art == 'teilnahme':
            return bool(self.finde_anzahl(art))
        elif art == 'livestream':
            return bool(self.link) and bool(self.ob_livestream)
        elif art == 'aufzeichnung':
            return bool(self.datei) and bool(self.ob_aufzeichnung)
        else:
            return ValueError('Art %s habe ich noch nicht beachtet' % art)

    def __str__(self):
        return self.art_veranstaltung.bezeichnung+': '+self.bezeichnung

    def hat_medien(self):
        """ gibt Liste der art-Namen, die aktiv sind, zurück; also insb.
        leere Liste die in if-Abfrage False gibt """
        medien = [art for art in ['livestream', 'aufzeichnung']
            if self.anzeigemodus(art) != 'verbergen']
        return medien

    def embed_link(self):
        return self.link.replace('watch?v=', 'embed/')

    def ist_vergangen(self):
        return self.datum < date.today()

    def ist_zukunft(self):
        return self.datum >= date.today()

    def ist_bald(self, tage=4):
        return True if 0 <= (self.datum - date.today()).days < tage else False


class Studiumdings(KlasseMitProdukten):
    beschreibung1 = models.TextField()
    beschreibung2 = models.TextField()
    reihenfolge = models.SmallIntegerField(null=True)
    arten_liste = ['buchung']
    class Meta:
        verbose_name_plural = "Studienprogramme"
        verbose_name = "Studienprogramm"
        ordering = ['reihenfolge']

    def get_absolute_url(self):
        return reverse('studium_detail', kwargs={'slug': self.slug})

class ArtDerVeranstaltung(Grundklasse):
    beschreibung = models.TextField(
        max_length=1200,
        null=True, blank=True)
    preis_teilnahme = models.SmallIntegerField()
    # Achtung, hier Felder einfügen wenn mehr Arten von Medien dazukommen
    preis_livestream = models.SmallIntegerField(null=True, blank=True)
    preis_aufzeichnung = models.SmallIntegerField(null=True, blank=True)

    max_teilnehmer = models.SmallIntegerField(null=True, blank=True)
    zeit_beginn = models.TimeField()
    zeit_ende = models.TimeField()
    class Meta:
        verbose_name_plural = "Arten der Veranstaltungen"

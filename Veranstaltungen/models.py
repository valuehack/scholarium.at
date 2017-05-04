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
import random, string

class ArtDerVeranstaltung(Grundklasse):
    beschreibung = models.TextField(
        max_length=1200, 
        null=True, blank=True)    
    preis_praesenz = models.SmallIntegerField()
    preis_livestream = models.SmallIntegerField(null=True, blank=True)
    preis_aufzeichnung = models.SmallIntegerField(null=True, blank=True)
    max_teilnehmer = models.SmallIntegerField(null=True, blank=True)
    zeit_beginn = models.TimeField()
    zeit_ende = models.TimeField()
    class Meta:
        verbose_name_plural = "Arten der Veranstaltungen"
    
class Veranstaltung(KlasseMitProdukten):
    beschreibung = models.TextField()
    datum = models.DateField()
    art_veranstaltung = models.ForeignKey(ArtDerVeranstaltung)
    class Meta:
        verbose_name_plural = "Veranstaltungen"
    
    liste_arten = [1, 2]
    def preis_ausgeben(self, art):
        """ Preis ausgeben, je nach Veranstaltung und art (Format) """
        #if self.preis:
        #    return self.preis
        
        art = int(art)
        if art == 1:
            return self.art_veranstaltung.preis_praesenz
        elif art == 2: 
            return self.art_veranstaltung.preis_aufzeichnung
    
    def get_url(self):
        if self.art_veranstaltung.bezeichnung == 'Salon':
            return '/salon/%s' % self.slug
        elif self.art_veranstaltung.bezeichnung == 'Seminar':
            return '/seminar/%s' % self.slug

class Studiumdings(KlasseMitProdukten):
    beschreibung1 = models.TextField()
    beschreibung2 = models.TextField()
    class Meta:
        verbose_name_plural = "Studiendinger"
    
    def get_preis(self):
        return "Noch nicht implementiert"
    
class Medium(KlasseMitProdukten):
    gehoert_zu = models.ForeignKey(Veranstaltung, null=True, blank=True)
    datei = models.FileField()
    link = models.URLField(null=True, blank=True)
    # folgendes v.a. relevant wenn keine Veranstaltung verknüpft ist:
    typ = models.CharField(max_length=30, null=True, blank=True)
    beschreibung = models.TextField(max_length=2000, null=True, blank=True)
    datum = models.DateField(blank=True, null=True)
    
    def get_preis(self):
        if self.gehoert_zu:
            return self.gehoert_zu.art_veranstaltung.preis_aufzeichnung
        else:
            return 999
    
    class Meta:
        verbose_name_plural = "Medien"
    
    def __str__(self):
        return '{} ({})'.format(self.bezeichnung, self.slug) 
        
    def save(self, **kwargs):
        self.beschreibung = self.beschreibung or self.gehoert_zu.beschreibung
        self.bezeichnung = self.bezeichnung or self.gehoert_zu.bezeichnung
        self.typ = self.typ or self.gehoert_zu.art_veranstaltung
        self.datum = self.datum or self.gehoert_zu.datum
        if not self.pk:
            self.slug = ''.join(random.sample(string.ascii_lowercase, 12))
        super().save(**kwargs)
        

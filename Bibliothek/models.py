"""

"""

from django.db import models
from Produkte.models import KlasseMitProdukten

class Altes_Buch(KlasseMitProdukten):
    arten_liste = ['kaufen']
    autor_und_titel = models.CharField(
        max_length=255,
        null=True, blank=True)
    def button_text(self, _):
        return 'Auswählen!'


class Buch(KlasseMitProdukten):
    arten_liste = ['kaufen', 'leihen', 'druck', 'pdf', 'mobi', 'epub'] #
    # druck bedeutet neu und kaufen ist ein gebrauchtes Bibliotheksbuch
    titel = models.CharField(
        max_length=255,
        null=True, blank=True)
    autor = models.CharField(
        max_length=255,
        null=True, blank=True)
    isbn = models.CharField(
        max_length=40,
        null=True, blank=True)
    adresse = models.CharField(
        max_length=100,
        null=True, blank=True)
    ausgabe = models.CharField(
        max_length=100,
        null=True, blank=True)
    herausgeber = models.CharField(
        max_length=100,
        null=True, blank=True)
    serie = models.CharField(
        max_length=100,
        null=True, blank=True)
    notiz = models.CharField(
        max_length=100,
        null=True, blank=True)
    jahr = models.CharField(
        max_length=4,
        null=True, blank=True)
    sprache = models.CharField(
        max_length=3,
        null=True, blank=True)
    exlibris = models.CharField(
        max_length=40,
        null=True, blank=True)
    stichworte = models.CharField(
        max_length=255,
        null=True, blank=True)
    zusammenfassung = models.TextField(
        null=True, blank=True)
    pdf = models.FileField(upload_to='buecher', null=True, blank=True)
    epub = models.FileField(upload_to='buecher', null=True, blank=True)
    mobi = models.FileField(upload_to='buecher', null=True, blank=True)
    bild = models.ImageField(upload_to='buecher', null=True, blank=True)
    alte_nr = models.SmallIntegerField(null=True, editable=False)

    def preis_ausgeben(self, art):
        if art=='leihen':
            return self.finde_preis(art) or 13
        elif art=='kaufen':
            return self.finde_preis(art) or 37
        elif art in ['pdf', 'epub', 'mobi']:
            return self.finde_preis(art) or 5
        elif art=='druck':
            return self.finde_preis(art) or 20

    def button_text(self, art):
        return '%s!' % art.capitalize()

    def save(self, *args, **kwargs):
        if not self.bezeichnung:
            self.bezeichnung = "%s: %s" % (self.autor, self.titel)
        return super().save(*args, **kwargs)

    def anzeigemodus(self, art):
        from Produkte.models import arten_attribute
        if arten_attribute[art][0] and self.finde_anzahl(art) > 1:
            return 'mit_menge'
        elif arten_attribute[art][0] and self.finde_anzahl(art) == 0:
            return 'verbergen'
        else:
            return 'inline'

    class Meta:
        verbose_name_plural = 'Bücher'

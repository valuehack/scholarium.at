"""
Modelle für Produkt und die Grundklasse für Veranstaltungen etc., aus der man
dann leicht Produkte erstellen können soll.
"""

from django.db import models
from seite.models import Grundklasse


class KlasseMitProdukten(Grundklasse):
    def erstelle_produkt(self):
        attribut_name = 'zu_'+self.__class__.__name__.lower()
        p = Produkt(bezeichnung=self.bezeichnung)
        p.__setattr__(attribut_name, self)
        p.save()
        return None

    def save(self):
        if not self.id:
            super().save()
            self.erstelle_produkt()
        else:
            super().save()

    class Meta:
        abstract = True


class Produkt(Grundklasse):
    zu_veranstaltung = models.ForeignKey(
        "Veranstaltungen.Veranstaltung",
        null=True, blank=True,
        on_delete=models.SET_NULL)
    zu_medium = models.ForeignKey(
        "Veranstaltungen.Medium",
        null=True, blank=True,
        on_delete=models.SET_NULL)
#    zu_buechlein = models.ForeignKey(
#        "Scholien.Buechlein",
#        null=True, blank=True,
#        on_delete=models.SET_NULL)
#    zu_buch = models.ForeignKey(
#        "Bibliothek.Buch",
#        null=True, blank=True,
#        on_delete=models.SET_NULL)
    preis = models.SmallIntegerField(blank=True, null=True)
    kaeufe = models.ManyToManyField(
        'Grundgeruest.ScholariumProfile',
        through='Kauf',
        editable=False)

    # vielleicht ist das Quatsch, weil gedoppelt mit zu_xy-Attribut
    art_choices = [('Teilnahme', )*2,
        ('Livestream', )*2,
        ('Videoaufzeichnung', )*2,
        ('Audioaufzeichnung', )*2, ]
    art_produkt = models.CharField(
        max_length=25,
        choices=art_choices,
        default='')

    @property
    def get_preis(self):
        if self.preis: # Achtung Preis=0 kommt nicht in diesen Ast
            print('eigener')
            return self.preis
        elif self.zu_veranstaltung:
            print('von veranstaltung')
            return self.zu_veranstaltung.get_preis()
        elif self.zu_medium:
            print('von medium')
            return self.zu_medium.get_preis()
        else:
            return 888

    def __str__(self):
        if self.zu_veranstaltung:
            return 'Teilnahme an {}'.format(self.zu_veranstaltung)
        elif self.zu_medium:
            return 'Medium zu {}'.format(self.zu_medium)
        else:
            return 'Produkt: weder eine Teilnahme noch ein Medium, bitte Produkt.__str__() anpassen'
    
    class Meta:
        verbose_name_plural = 'Produkte'


class Kauf(models.Model):
    nutzer = models.ForeignKey(
        'Grundgeruest.ScholariumProfile',
        on_delete=models.SET_NULL,
        null=True)
    produkt = models.ForeignKey(
        Produkt,
        on_delete=models.SET_NULL,
        null=True)
    menge = models.SmallIntegerField(blank=True, default=1)
    zeit = models.DateTimeField(
        auto_now_add=True,
        editable=False)
    # falls was schief geht, wird das Guthaben gecached:
    guthaben_davor = models.SmallIntegerField(editable=False)

    def __str__(self):
        return 'Kauf von {}, {}: {}'.format(
            self.nutzer.user.__str__(),
            self.zeit.strftime('%x, %H:%M'),
            self.produkt.__str__())

    class Meta():
        verbose_name_plural = 'Käufe'

class Spendenstufen(Grundklasse):
    spendenbeitrag = models.SmallIntegerField()
    beschreibung = models.TextField()
    gegenwert1 = models.TextField(null=True, blank=True)
    gegenwert2 = models.TextField(null=True, blank=True)
    gegenwert3 = models.TextField(null=True, blank=True)
    gegenwert4 = models.TextField(null=True, blank=True)
    gegenwert5 = models.TextField(null=True, blank=True)
    gegenwert6 = models.TextField(null=True, blank=True)
    class Meta:
        verbose_name_plural = "Spendenstufen"

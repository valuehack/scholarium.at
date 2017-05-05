"""
Modelle für Produkt und die Grundklasse für Veranstaltungen etc., aus der man
dann leicht Produkte erstellen können soll.
"""

from django.db import models
from django.contrib.contenttypes.models import ContentType
from seite.models import Grundklasse


class KlasseMitProdukten(Grundklasse):
    def erstelle_produkt(self):
        """ veraltet, bald löschen """
        attribut_name = 'zu_'+self.__class__.__name__.lower()
        p = Produkt(bezeichnung=self.bezeichnung)
        p.__setattr__(attribut_name, self)
        p.save()
        return None
    
    # evtl. zu überschreiben, Liste der Formate, für Schleife im Template
    liste_arten = [0]
    
    def pk_ausgeben(self):
        """ Gibt die Kennung des Produktes (contenttype, id), wie es der 
        Warenkorb-Item braucht, zurück, dahinter muss noch die art. Zur 
        Verwendung in Templates. 
        Da muss noch was geändert werden, ist nicht DRY, vermutlich die 
        Funktionen tupel_zu_pk und tupel_aus_pk von der Item-Klasse nach 
        hier angepasst verschieben? """
        return '; '.join([
            self.__class__.__name__.lower(), 
            str(self.pk), 
            '',
        ])
    
    def preis_ausgeben(self, art):
        """ Default-Implementation einer Preis-Funktion, die sollte bei 
        jeder Klasse überschrieben werden. Grundsätzlich sollten nur 
        Klassen, die nur eine Art haben den Parameter art==0 akzeptieren;
        wenn es mehrere gibt, dann heißen die zur Vermeidung von Fehlern 
        1 bis n """
        if art == 0:
            return 0
        else: 
            return 999
        
    def save(self, **kwargs):
        """ auch bald löschen? """
        if not self.id:
            super().save(**kwargs)
            self.erstelle_produkt()
        else:
            super().save(**kwargs)

    class Meta:
        abstract = True


class Produkt(Grundklasse):
    """ brauchen wir nicht mehr, bald löschen """
    zu_veranstaltung = models.ForeignKey(
        "Veranstaltungen.Veranstaltung",
        null=True, blank=True,
        on_delete=models.SET_NULL)
    zu_medium = models.ForeignKey(
        "Veranstaltungen.Medium",
        null=True, blank=True,
        on_delete=models.SET_NULL)
    zu_studiumdings = models.ForeignKey(
        "Veranstaltungen.Studiumdings",
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
    #kaeufe = models.ManyToManyField(
    #    'Grundgeruest.ScholariumProfile',
    #    through='Kauf',
    #    editable=False)

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
        elif self.zu_studiumdings:
            return 'Studium: {}'.format(self.zu_studiumdings)
        else:
            return 'Produkt: nicht Teilnahme/Medium/Studium, bitte Produkt.__str__() anpassen'
    
    class Meta:
        verbose_name_plural = 'Produkte'


class Kauf(models.Model):
    nutzer = models.ForeignKey(
        'Grundgeruest.ScholariumProfile',
        on_delete=models.SET_NULL,
        null=True)
    produkt_model = models.ForeignKey(
        ContentType,
        on_delete=models.SET_NULL,
        null=True,)
    produkt_id = models.SmallIntegerField(null=True)
    produkt_art = models.SmallIntegerField(null=True)
    menge = models.SmallIntegerField(blank=True, default=1)
    zeit = models.DateTimeField(
        auto_now_add=True,
        editable=False)
    # falls was schief geht, wird das Guthaben gecached:
    guthaben_davor = models.SmallIntegerField(editable=False)

    def __str__(self):
        return 'Kauf von {} am {}: {} Nr. {} im Format {}'.format(
            self.nutzer.user.__str__(),
            self.zeit.strftime('%x, %H:%M'),
            self.produkt_model.__str__(), 
            self.produkt_id, 
            self.produkt_art)

    class Meta():
        verbose_name_plural = 'Käufe'

class Spendenstufe(Grundklasse):
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

    def gegenwerte_html(self):
        gegenwerte = []
        for i in range(1, 7):
            if getattr(self, 'gegenwert%s' % i):
                gegenwerte.append(getattr(self, 'gegenwert%s' % i))
        return gegenwerte
        

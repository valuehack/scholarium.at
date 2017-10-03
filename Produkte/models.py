"""
Modelle für Produkt und die Grundklasse für Veranstaltungen etc., aus der man
dann leicht Produkte erstellen können soll.
"""

import json, six, functools
from django.db import models
from django.contrib.contenttypes.models import ContentType
from seite.models import Grundklasse
from django.db.models.base import ModelBase


class PreiseMetaklasse(ModelBase):
    """ Metaklasse, die die Metaklasse ModelBase aufruft
    Soll der KlasseMitProdukten (und allen Erben) Felder für den Preis und
    die Mengen der Produktarten hinzufügen. Nutzt dazu Einträge der in den
    Klassen gesetzte arten_liste.
    Das ist so kompliziert, damit dynamisch (aus der arten_liste als DRY
    Datenquelle) automatisch alles erzeugt wird (und der Nutzer, der neu
    von KlasseMitProdukt erbt das nicht vergessen kann)
    (vermutlich hätte auch __init_subclass__() zu verwenden geklappt, wäre
    auch einfacher, habe ich aber erst später gefunden
    """
    def __new__(cls, name, parents, attribute):
        super_new = super().__new__ # der Konstruktor von ModelBase
        NeueKlasse = super_new(cls, name, parents, attribute)

        def setze_anzahl(self, art, anzahl):
            setattr(self, 'anzahl_'+art, anzahl)

        def setze_preis(self, art, preis):
            setattr(self, 'preis_'+art, preis)

        def finde_anzahl(self, art):
            return getattr(self, 'anzahl_'+art)

        def finde_preis(self, art):
            return getattr(self, 'preis_'+art)

        fkts = [setze_anzahl, finde_anzahl, setze_preis, finde_preis]

        # für KlasseMitProdukten allgemeine Funktionen setzen, die werden
        # an die Kinder vererbt; spezielle Funktionen erst bei den Kindern
        # setzen und vor allem Felder nur bei Kindern initialisieren
        if name=='KlasseMitProdukten':
            for fkt in fkts:
                setattr(NeueKlasse, fkt.__name__, fkt)
        else:
            for art in NeueKlasse.arten_liste:
                NeueKlasse.add_to_class(
                    'preis_%s' % art,
                    models.SmallIntegerField(null=True, blank=True))
                if arten_attribute[art][0]: # wenn beschränkt
                    NeueKlasse.add_to_class(
                        'anzahl_%s' % art,
                        models.SmallIntegerField(default=0, blank=True))
                else: # sonst keine Anzahl, sondern boolean ob aktiv
                    NeueKlasse.add_to_class(
                        'ob_%s' % art,
                        models.BooleanField(default=0, blank=True))
                for fkt in fkts:
                    setattr(NeueKlasse,
                        fkt.__name__+'_'+art,
                        functools.partialmethod(fkt, art))

        return NeueKlasse


# globale Attribute für Produktarten; zu jeder Art ein Tupel aus
# ob_beschränkt, button_text
arten_attribute = {
    'teilnahme': (5, 'Auswählen', 'Vor Ort'),
    'livestream': (False, 'Livestream buchen', 'Livestream'),
    'aufzeichnung': (False, 'Aufzeichnung ansehen und/oder mp3 herunterladen', 'MP3'),
    'pdf': (False, 'PDF'),
    'epub': (False, 'EPUB'),
    'mobi': (False, 'Kindle'),
    'druck': (10, 'Druck'),
    'kaufen': (1, 'Zum Kauf auswählen'),
    'leihen': (1, 'Zum Verleih auswählen'),
}

class KlasseMitProdukten(Grundklasse, metaclass=PreiseMetaklasse):
    """ Von dieser Klasse erbt alles, was man in den Warenkorb legen kann
    """

    """ Liste aller möglichen Formate der Produktklasse """
    arten_liste = ['spam'] # Liste von <art> str

    def anzeigemodus(self, art=0):
        """ gibt einen Code für den Anzeigemodus in Templates aus; also ob
        es gar nicht angezeigt, oder ausgegraut, oder richtig """
        if art not in self.arten_liste:
            raise ValueError('Anzeigemodus: Bitte gültige Art angeben')
        if self.__class__.__name__ == "Buechlein":
            if art=="druck" and self.finde_anzahl(art) == 0:
                return "verbergen"
            elif art!="druck" and getattr(self, "ob_"+art)==False:
                return "verbergen"
            else:
                return "inline" # unabhängig von der art

        if arten_attribute[art][0]: # falls beschränkt
            if self.finde_anzahl(art) == 0 and art=='teilnahme':
                modus = 'ausgegraut' # ausgebuchte Veranstaltung
            elif art=='teilnahme':
                modus = 'mit_menge' # Veranstaltung mit select-box
            # sonst nicht teilnahme, also nur beschränktes Buch (?)
            #elif self.finde_anzahl(art) == 0:
            #    modus = 'verbergen'
            else:
                modus = 'inline'
        else:
            if getattr(self, 'ob_'+art):
                modus = 'ohne_menge'
            else:
                modus = 'verbergen'

        return modus

    def arten_aktiv(self):
        aktiv = []
        for art in self.arten_liste:
            if self.anzeigemodus(art) != 'verbergen':
                aktiv.append(art)
        return aktiv

    def pk_ausgeben(self, art=0):
        """ Gibt die pk (für Warenkorb-Item) zurück
        Wird vom Templatetag {% produkt_pk <art> %} genutzt.
        """
        return Kauf.obj_zu_pk(self, art)

    def preis_ausgeben(self, art=0):
        """ Default-Implementation einer Preis-Funktion, die vom Warenkorb-
        Item verwendet wird. Kann bei jeder Klasse überschrieben werden.
        Wird auch vom Templatetag {% preis <art> %} genutzt. """
        if art not in self.arten_liste:
            raise ValueError('Bitte gültige Art für Preis angeben')
        else:
            return self.finde_preis(art)

    def button_text(self, art=0):
        """ Gibt Beschriftung für Button zum in-den-Warenkorb-Legen aus """
        return arten_attribute[art][1]

    def anzahlen_ausgeben(self, art=0):
        """ Gibt range der Anzahlen für dropdown im Template zurück """
        if art not in self.arten_liste:
            raise ValueError('Bitte gültige Art für Menge angeben')

        if arten_attribute[art][0]: # falls beschränkt
            if self.finde_anzahl(art) == 0:
                return 0
            else:
                anz = 1 + min(arten_attribute[art][0], self.finde_anzahl(art))
                return range(1, anz)
        else:
            return None

    def ob_gekauft_von(self, kunde, art):
        for k in kunde.kauf_set.all():
            if k.art_ausgeben()==art and int(k.obj_pk_ausgeben())==self.pk:
                return True
        return False

    def format_text(self, art=0):
        """Gibt für Veranstaltungen den Text des jeweiligen Formats aus"""
        return arten_attribute[art][2]

    class Meta:
        abstract = True


class Kauf(models.Model):
    """ Verknüpft Nutzer und Waren (im Form von 3-teiliger pk gespeichert)

    Die Klasse soll die definitive source of information für alle Methoden,
    die mit der Konversion von pk und Objekten und mit der Ausgabe der
    Eigenschaften zu tun haben, sein.
    views.Warenkorb erbt ein paar Methoden, und in den Templates sollen sie
    genutzt werden um alle Daten zum Objekt des Kaufs zu bekommen.
    """
    nutzer = models.ForeignKey(
        'Grundgeruest.ScholariumProfile',
        on_delete=models.SET_NULL,
        null=True)
    produkt_pk = models.CharField(max_length=40)
    menge = models.SmallIntegerField(blank=True, default=1)
    zeit = models.DateTimeField(
        auto_now_add=True,
        editable=False)
    kommentar = models.CharField(max_length=255, blank=True)
    # falls was schief geht, wird das Guthaben gecached:
    guthaben_davor = models.SmallIntegerField(editable=False, null=True)


    # 2 Hilfsfunktionen um pk in drei Teile zu spalten und zurück:
    @staticmethod
    def tupel_aus_pk(pk):
        model_name, obj_pk, art = str(pk).split('+')
        return model_name, obj_pk, art

    @staticmethod
    def tupel_zu_pk(tupel_pk):
        model_name, obj_pk, art = [str(x) for x in tupel_pk]
        return '+'.join([model_name, obj_pk, art])

    # von der pk auf's Objekt zugreifen und rückwärts pk kostruieren:
    @staticmethod
    def obj_aus_pk(pk):
        """ Liest Objekt aus dem übergebenen pk aus
        pk wird in drei Teile zerlegt und die ersten beiden verwendet
        um die Tabelle an der richtigen Zeile auszulesen
        """
        model_name, obj_pk, art = Kauf.tupel_aus_pk(pk)
        objekt = ContentType.objects.get(
            model=model_name).get_object_for_this_type(
            pk=obj_pk)
        return objekt

    @staticmethod
    def obj_zu_pk(objekt, art=0):
        """ Erzeugt zu einem Objekt (und art) die Kennung des Produktes
        (contenttype, id), und gibt den pk, wie es der Warenkorb-Item
        braucht, zurück.
        """
        return Kauf.tupel_zu_pk([
            objekt.__class__.__name__.lower(),
            str(objekt.pk),
            str(art),
        ])

    def pk_ausgeben(self):
        """ Gibt pk des 'verknüpften' Objektes als string aus """
        return self.produkt_pk

    def tupel_ausgeben(self):
        """ Gibt pk des 'verknüpften' Objektes als string aus """
        return self.tupel_aus_pk(self.pk_ausgeben())

    def model_ausgeben(self):
        """ Gibt den model-Namen des 'verknüpften' Objektes aus """
        return self.tupel_ausgeben()[0]

    def obj_pk_ausgeben(self):
        """ Gibt die pk des 'verknüpften' Objektes (nicht des Kaufes!) aus """
        return self.tupel_ausgeben()[1]

    def art_ausgeben(self):
        """ Gibt die Nr der Art des 'verknüpften' Objektes aus """
        return self.tupel_ausgeben()[2]

    def objekt_ausgeben(self, mit_art=False):
        """ Gibt das 'verknüpfte' Objekt zurück, das was django bei einem
        ForeignKey sonst automatisch erledigen würde """
        if mit_art:
            return self.obj_aus_pk(self.produkt_pk), self.art_ausgeben()
        else:
            return self.obj_aus_pk(self.produkt_pk)

    @staticmethod
    def kauf_ausfuehren(nutzer, pk, ware):
        """ Führt die Kaufabwicklung aus, d.h. legt ein neues Kauf-Objekt
        an und zieht dem Nutzer Guthaben ab. Muss einen Warenkorb-Item
        übergeben bekommen, da dort die Menge steht und .total() genutzt
        wird für den Preis.
        *** offen: Sollte der Ware Anzahl abziehen, falls beschränkt! """
        guthaben = nutzer.guthaben
        kauf = Kauf.objects.create(
            nutzer=nutzer,
            produkt_pk=pk,
            menge=ware.quantity,
            guthaben_davor=guthaben)
        nutzer.guthaben = guthaben - ware.total
        nutzer.save()
        return kauf

    @classmethod
    def neuen_anlegen(cls, objekt, art, menge, kunde, kommentar):
        """ Erstellt neuen Kauf für die Historie. In erster Linie für den
        Import aus der alten DB gebraucht. Keine Modifikation der Menge
        oder des Guthabens, nur Kauf-objekt. """

        pk = cls.obj_zu_pk(objekt, art)
        kauf = cls.objects.create(
            nutzer=kunde,
            produkt_pk=pk,
            menge=menge,
            kommentar=kommentar)
        return kauf

    def __str__(self):
        objekt, art = self.objekt_ausgeben(mit_art=True)
        text = '{} hat am {} gekauft: {}'.format(
            self.nutzer.user.__str__(),
            self.zeit.strftime('%x, %H:%M'),
            objekt.__str__())
        if art != 0:
            text += ' im Format {}'.format(art)

        return text

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

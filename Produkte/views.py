from django.shortcuts import get_object_or_404, render
from django.http import HttpResponse, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.http import JsonResponse
import pdb
from django.contrib import messages

# Create your views here.

from easycart import BaseCart, BaseItem
from Grundgeruest.views import erstelle_liste_menue
from .models import Kauf, arten_attribute
from Veranstaltungen.models import Veranstaltung

"""
Integration des Pakets easycart - keine Modelle, über session Variablen

Idee der built-in-Implementation:
 - warenkorb wird in der session als JSON-string gespeichert
 - für Bearbeitung wird der Konstruktor von BaseCart aufgerufen und bekommt
   den request, und damit die session, übergeben
 - zum Speichern wird cart.encode() ausgeführt um das rückwärts auszuführen
 - im kodierten Zustand haben wir im Wesentlichen ein dict (pk -> quantity)
 - pk bezieht sich auf ein Modell, also alle Produkte in einer DB-Tabelle
 - im geladenen Zustand eine Instanz von Cart, cart.items ist ein dict von
   Items, die wiederum haben item.obj (Instanz vom Produkt-Modell) und
   item.quantity
 - Preis wird aus einem Attribut der obj-Instanz ausgelesen, mit Methoden
   von Item und Cart validiert und von Cart aus aufgerufen
 - beim Laden wird eine Cart instanziiert aus request; cart.create_items()
   instantiiert die items, wobei cart.get_queryset(pks) aufgerufen wird und
   den DB-lookup ausführt um die item.obj zu befüllen.
 - auch bei add/change_quantity wird get_queryset() aufgerufen
 - konkret aufgerufen werden die Methoden, indem die url an den view weiter
   leitet, der mit den POST-Parameter die Fkt der Cart-Instanz aufruft.
 - offene Frage: wann wird Cart instantiiert, bei Severstart, oder...?


Änderungen:
 - nur ein pk ist unbefriedigend, wir haben ein Tupel von drei:
   art (Veranstaltung/Buch/etc) + id + typ (Teilnahme/Livestream)
 - es muss offensichtlich get_queryset() und encode() geändert werden, da
   item.obj jetzt aus zwei Werten (Tabelle und Zeile) gelesen wird. Eine
   Menge anderes gibt dann auch probleme; elegante Lösung s. unten...
 - zur Philosophie: ist ein "tradeoff" ... ist nicht schön, dass die Klasse
   Veranstaltung Daten enthält, die nix mit der Veranstaltung zu tun haben,
   wie Preis oder besetzte Plätze; aber alternativ muss man zu jedem Objekt
   ein extra Produkt erstellen, welches (zumeist leere) Verknüpfungen zu
   den verschiedenen produktfähigen Klassen hat...
 - Konkret die Umsetzung, um möglichst wenig zu ändern. Ist viiel einfacher
   als es ursprünglich schien:
   - der Item-Konstruktor bekommt die art als kwarg übergeben, speichert
     sie automatisch in der Item-Instanz.
   - sowohl das items-dict der Cart als auch die session_items bekommen
     als keys die kombinierten Strings mit drei Werten.
   - für die Erstellung der Item-Instanzen aus der session sind also nur
     kleine Details zu ändern.
   - die url für add verweist auf neuen view, der die pk zerteilt und
     sowohl den ganzen pk (die braucht die Cart-Instanz um die als keys
     der items-dict zu nehmen) als auch die art (die wird als optionaler
     kwarg interpretiert und automatisch an den Item-Konstruktor weiter
     geleitet) zurück. So muss ich nur get_queryset und encode ändern, und
     den Konstruktor und __repr__ vom Item.
     - Cart.add bekommt die Parameter pk, quantity, art, holt sich obj
     über die pk, und fügt Item(...) zum items-dict unter dem key pk hinzu.
"""

class Ware(BaseItem):
    def __init__(self, obj, quantity=1, **kwargs):
        if not 'art' in kwargs:
            kwargs.update([('art', 1)])
        self._quantity = self.clean_quantity(quantity)
        #pdb.set_trace()
        self.price = obj.preis_ausgeben(kwargs['art'])
        self.obj = obj
        self.art = kwargs['art']
        for key, value in kwargs.items():
            setattr(self, key, value)
        self._kwargs = kwargs

    def __repr__(self):
        main_args = 'obj={}, art={}, quantity={}'.format(
            self.obj,
            self._kwargs['art'],
            self.quantity)
        extra_args = ['{}={}'.format(k, getattr(self, k)) for k in self._kwargs]
        args_repr = ', '.join([main_args] + extra_args)
        return  '<Ware: ' + args_repr + '>'

    def model_ausgeben(self):
        return self.obj.__class__.__name__.lower()

class Warenkorb(BaseCart):
    item_class = Ware

    @staticmethod
    def tupel_aus_pk(pk):
        return Kauf.tupel_aus_pk(pk)

    @staticmethod
    def tupel_zu_pk(tupel_pk):
        return Kauf.tupel_zu_pk(tupel_pk)

    def items_ausgeben(self):
        """ gibt pk-ware-Paare zurück; brauche ich im Template, da sonst
        die Items nicht initialisiert sind """
        return list(self.items.items())

    def get_queryset(self, pks):
        """ Gibt Liste der Objekte zu den übergebenen pks zurück """
        objekte = []
        for pk in pks:
            objekte.append(Kauf.obj_aus_pk(pk))
        return objekte

    def encode(self, formatter=None):
        """ fast übernommen aus der Ursprungsimplementierung
        Nur Konstruktion von pk (als key für items verwendet) erweitert


        Return a representation of the cart as a JSON-response.

        Parameters
        ----------
        formatter : func, optional
            A function that accepts the cart representation and returns
            its formatted version.

        Returns
        -------
        django.http.JsonResponse

        Examples
        --------
        Assume that items with primary keys "1" and "4" are already in
        the cart.

        >>> cart = Cart(request)
        >>> def format_total_price(cart_repr):
        ...     return intcomma(cart_repr['totalPrice'])
        ...
        >>> json_response = cart.encode(format_total_price)
        >>> json_response.content
        b'{
            "items": {
                '1': {"price": 100, "quantity": 10, "total": 1000},
                '4': {"price": 50, "quantity": 20, "total": 1000},
            },
            "itemCount": 2,
            "totalPrice": "2,000",
        }'

        """
        items = {}
        # The prices are converted to strings, because they may have a
        # type that can't be serialized to JSON (e.g. Decimal).
        for item in self.items.values():
            model_name = item.obj.__class__.__name__.lower()
            obj_pk = item.obj.pk
            art = item._kwargs['art']
            pk = self.tupel_zu_pk((model_name, obj_pk, art))
            items[pk] = {
                'price': str(item.price),
                'quantity': item.quantity,
                'total': item.total,
            }
        cart_repr = {
            'items': items,
            'itemCount': self.item_count,
            'totalPrice': str(self.total_price),
        }
        if formatter:
            cart_repr = formatter(cart_repr)
        return JsonResponse(cart_repr)

    def create_items(self, session_items):
        """fast übernommen aus der Ursprungsimplementierung
        Nur verhindert, dass pk (als key für items verwendet) mit obj.pk
        überschrieben wird; vorher war die Funktion dafür nicht darauf
        angewiesen, dass get_queryset die obj zu den pks in der passenden
        Reihenfolge zurückgibt; das tut's aber jetzt (war ursprünglich
        queryset, bei mit Liste), insofern ist das okay.

        Instantiate cart items from session data.

        The value returned by this method is used to populate the
        cart's `items` attribute.

        Parameters
        ----------
        session_items : dict
            A dictionary of pk-quantity mappings (each pk is a string).
            For example: ``{'1': 5, '3': 2}``.

        Returns
        -------
        dict
            A map between the `session_items` keys and instances of
            :attr:`item_class`. For example::

                {'1': <CartItem: obj=foo, quantity=5>,
                 '3': <CartItem: obj=bar, quantity=2>}

        """
        pks = list(session_items.keys())
        items = {}
        item_class = self.item_class
        process_object = self.process_object
        # die eine Zeile geändert:
        for pk, obj in zip(pks, self.get_queryset(pks)):
            obj = process_object(obj)
            items[pk] = item_class(obj, **session_items[pk])
        if len(items) < len(session_items):
            self._stale_pks = set(session_items).difference(items)
        return items

    @property
    def ob_versand(self):
        for item in self.items.values():
            if arten_attribute[item.art][0] and item.art != 'teilnahme': # wenn max. Anzahl angegeben
                return True

        return False

    def count_total_price(self):
        """ kopiert; berechnet die Summe. Änderung: addiere 5 wenn unter
        den Bestellungen Drucksachen sind """
        summe = sum((item.total for item in self.items.values()))
        return summe + self.ob_versand * 5


@login_required
def bestellungen(request):
    """ Übersicht der abgeschlossenen Bestellungen

    Es werden die Käufe vom Nutzer gesucht und in einem dict nach
    Kategorien geordnet ausgegeben, folgende Kategorien:
     - kommende Veranstaltungen
     - elektronische Medien
     - unkategorisiert
    (später noch bestellte Bücher)
    """
    nutzer = request.user.my_profile
    liste_menue = erstelle_liste_menue(request.user)
    liste_kaeufe = list(Kauf.objects.filter(nutzer=nutzer))
    # hack: bestimme, welche pks existieren, sonst gibt's Fehler, wenn die
    # Objekte gelöscht wurden; die werden unten in while-Schleife aussortiert
    liste_models = set([k.model_ausgeben() for k in liste_kaeufe])
    from django.contrib.contenttypes.models import ContentType
    pks_zu_model = dict([
        (name, ContentType.objects.get(model=name).model_class(
        ).objects.all().values_list('pk', flat=True))
        for name in liste_models
    ])

    # verteile Käufe nach Kategorie:
    kaeufe = {'teilnahmen': [], 'digital': [], 'rest': []}

    while liste_kaeufe:
        kauf = liste_kaeufe.pop()

        if int(kauf.obj_pk_ausgeben()) not in pks_zu_model[kauf.model_ausgeben()]:
            continue

        if (kauf.model_ausgeben() == 'veranstaltung' and
            kauf.art_ausgeben() == 'teilnahme' and
            kauf.tupel_aus_pk(kauf.pk_ausgeben())[1] in v_pks):
            kaeufe['teilnahmen'].append(kauf)
        elif kauf.art_ausgeben() in ['pdf', 'epub', 'mobi', 'aufzeichnung']:
            kaeufe['digital'].append(kauf)
        else:
            kaeufe['rest'].append(kauf)

    return render(request,
        'Produkte/bestellungen.html',
        {'kaeufe': kaeufe, 'liste_menue': liste_menue})

def kaufen(request):
    warenkorb = Warenkorb(request)
    nutzer = request.user.my_profile
    if nutzer.guthaben < warenkorb.count_total_price():
        messages.error(request, 'Ihr Guthaben reicht leider nicht aus. Laden Sie ihr Guthaben auf, indem Sie ihre Unterstützung erneuern.')
        return HttpResponseRedirect(reverse('Produkte:warenkorb'))

    for pk, ware in list(warenkorb.items.items()):
        Kauf.kauf_ausfuehren(nutzer, pk, ware)

    warenkorb.empty()

    return HttpResponseRedirect(reverse('Produkte:bestellungen'))


def medien_runterladen(request):
    """ bekommt als POST, welches Objekt heruntergeladen werden soll, prüft
    ob der user das darf, und gibt response mit Anhang zurück """
    from django.utils.encoding import smart_str
    import os
    from seite.settings import MEDIA_ROOT

    kauf = get_object_or_404(Kauf, id=request.POST['kauf_id'])
    if not kauf.nutzer.user == request.user:
        return 404
    # sonst setze fort, falls der Nutzer das darf:

    obj, art = kauf.objekt_ausgeben(mit_art=True)
    filefield = obj.datei if art=='aufzeichnung' else getattr(obj, art)
    with open(filefield.path, 'rb') as datei:
        medium = datei.read()

    name, ext = os.path.splitext(filefield.name)
    print(ext)

    response = HttpResponse(medium, content_type='application/force-download')
    response['Content-Disposition'] = ('attachment; filename=' +
        obj.slug + ext)

    return response


from easycart.cart import CartException
from django.views.generic import View

class CartView(View):
    """ kopiert aus easycart.views um den return-Wert zu ändern - statt
    cart.encode wird ein Redirect an warenkorb ausgegeben
    """
    action = None
    required_params = ()
    optional_params = {}

    def post(self, request):
        # Extract parameters from the post data
        params = {}
        for param in self.required_params:
            try:
                params[param] = request.POST[param]
            except KeyError:
                return JsonResponse({
                    'error': 'MissingRequestParam',
                    'param': param,
                })
        for param, fallback in self.optional_params.items():
            params[param] = request.POST.get(param, fallback)
        # Perform an action on the cart using these parameters
        cart = Warenkorb(request)
        action = getattr(cart, self.action)
        try:
            action(**params)
        except CartException as exc:
            return JsonResponse(dict({'error': exc.__class__.__name__},
                                     **exc.kwargs))

        return HttpResponseRedirect(reverse('Produkte:warenkorb'))


class AddItem(CartView):
    """ habe 'post()' fast aus easycart.views.CartView kopiert, etwas
    vereinfacht, da ja konkreter für "add" und die Warenkorb-Klasse, und
    das Übergeben von art hinzugefügt
    """

    def post(self, request):
        # Extract parameters from the post data
        params = {}
        try:
            params['pk'] = request.POST['pk']
        except KeyError:
            return JsonResponse({
                'error': 'MissingRequestParam',
                'param': 'pk',
            })

        params['quantity'] = request.POST.get('quantity', 1)

        # parameter art hinzufügen
        model_name, obj_pk, art = Warenkorb.tupel_aus_pk(params['pk'])
        params.update([('art', art)])

        # Perform an action on the cart using these parameters
        cart = Warenkorb(request)
        try:
            cart.add(**params)
        except CartException as exc:
            return JsonResponse(dict({'error': exc.__class__.__name__},
                                     **exc.kwargs))
        return HttpResponseRedirect(reverse('Produkte:warenkorb'))

class RemoveItem(CartView):
    """ kopiert aus easycart.views, nutzt lokales CartView """
    action = 'remove'
    required_params = ('pk',)


class EmptyCart(CartView):
    """ kopiert aus easycart.views, nutzt lokales CartView """
    action = 'empty'


class ChangeItemQuantity(CartView):
    """ kopiert aus easycart.views, nutzt lokales CartView """
    action = 'change_quantity'
    required_params = ('pk', 'quantity')

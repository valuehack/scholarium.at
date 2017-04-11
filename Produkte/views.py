from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required

# Create your views here.

from easycart import BaseCart, BaseItem
from Grundgeruest.views import erstelle_liste_menue
from .models import Kauf, Produkt
from .forms import ZahlungFormular

class Ware(BaseItem):
    PRICE_ATTR = 'get_preis'

class Warenkorb(BaseCart):
    item_class = Ware
    def get_queryset(self, pks):
        return Produkt.objects.filter(pk__in=pks)

@login_required
def bestellungen(request):
    nutzer = request.user.my_profile
    liste_menue = erstelle_liste_menue(request.user)
    kaeufe = Kauf.objects.filter(nutzer=nutzer)
    medien = [kauf for kauf in kaeufe if kauf.produkt.zu_medium]
    veranstaltungen = [kauf for kauf in kaeufe if kauf.produkt.zu_veranstaltung]
    return render(request, 
        'Produkte/bestellungen.html', 
        {'medien': medien, 
            'veranstaltungen': veranstaltungen, 
            'liste_menue': liste_menue,
        })

def kaufen(request):
    warenkorb = Warenkorb(request)
    nutzer = request.user.my_profile
    if nutzer.guthaben < warenkorb.count_total_price():
        return HttpResponse('Guthaben reicht nicht aus!') # das schöner machen!
    
    waren = warenkorb.list_items()
    for ware in waren:
        guthaben = nutzer.guthaben
        kauf = Kauf.objects.create(
            nutzer=nutzer,
            produkt_id=ware.obj.pk,
            menge=ware.quantity,
            guthaben_davor=guthaben)
        nutzer.guthaben = guthaben - ware.total
        nutzer.save()
        warenkorb.remove(ware.obj.pk)
        
    return HttpResponseRedirect(reverse('Produkte:warenkorb'))
    
def zahlen(request):
    # if this is a POST request we need to process the form data
    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        formular = ZahlungFormular(request.POST)
        # check whether it's valid:
        if formular.is_valid():
            # process the data in form.cleaned_data as required
            # ...
            # redirect to a new URL:
            return HttpResponseRedirect('/thanks/')

    # if a GET (or any other method) we'll create a blank form
    else:
        formular = ZahlungFormular()

    return render(request, 'Produkte/zahlung.html', {'formular': formular})    
    

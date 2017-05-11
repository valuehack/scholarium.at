from django import template
from Produkte.models import Kauf

register = template.Library()

@register.simple_tag
def preis(produkt, art=0):
    return produkt.preis_ausgeben(art)

@register.simple_tag
def produkt_pk(produkt, art=0):
    return produkt.pk_ausgeben(art)

@register.simple_tag
def ware_model(ware):
    return ware.obj.__class__.__name__.lower()

@register.simple_tag
def art_aus_pk(pk):
    return Kauf.tupel_aus_pk(pk)[2]

@register.simple_tag
def max_anzahl_zu_liste(max_anzahl=1):
    """ gibt Liste der Anzahlen 1..max zurück, bzw. die leere Liste, falls
    max_anzahl 1 oder False/None/etc ist """
    if max_anzahl and max_anzahl > 1:
        return range(1, max_anzahl+1)
    else: 
        return []

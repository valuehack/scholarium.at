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
def button_text(produkt, art=0):
    return produkt.button_text(art)

@register.simple_tag
def format_text(produkt, art=0):
    return produkt.format_text(art)

@register.simple_tag
def anzeigemodus(produkt, art=0):
    return produkt.anzeigemodus(art)

@register.simple_tag
def ware_model(ware):
    return ware.obj.__class__.__name__.lower()

@register.simple_tag
def art_aus_pk(pk):
    return Kauf.tupel_aus_pk(pk)[2]

@register.simple_tag
def max_anzahl_zu_liste(produkt, art=0):
    """ gibt Liste der Anzahlen 1..max zurück, falls das Produkt beschränkt
    ist, sonst None """
    return produkt.anzahlen_ausgeben(art)

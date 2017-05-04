from django import template

register = template.Library()

@register.simple_tag
def preis(produkt, art):
    return produkt.preis_ausgeben(art)

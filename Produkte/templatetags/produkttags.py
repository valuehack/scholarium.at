from django import template
from Produkte.models import Kauf
from Grundgeruest.models import ScholariumProfile

register = template.Library()

@register.simple_tag
def verbose(obj):
    return obj.__class__._meta.verbose_name

@register.simple_tag
def choice_value(key, field, formular):
    return dict(formular.fields[field].choices)[key]

@register.simple_tag
def stufenname(stufe):
    return dict(ScholariumProfile.stufe_choices)[int(stufe)]

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

@register.simple_tag
def ob_kaufbutton_zeigen(objekt, kunde, art):
    """ ob überhaupt ein Button zum Kaufen gezeigt wird; ob's ausgegraut
    ist, ist einne andere Frage. Momentan bei Veranstaltung angewendet. """
    from Produkte.models import arten_attribute
    if not kunde:
        return False
    if objekt.__class__.__name__ == "Veranstaltung" and art=='teilnahme':
        return not objekt.ist_vergangen()
    if arten_attribute[art][0]:
        return True

    return not objekt.ob_gekauft_von(kunde, art)


from Veranstaltungen.models import Veranstaltung, ArtDerVeranstaltung
@register.simple_tag
def ob_livestream_zeigen(veranstaltung, kunde):
    """ ob der livestream-Block im Detail-view zu sehen ist """
    salonart = ArtDerVeranstaltung.objects.get(bezeichnung="Salon")
    if not kunde:
        return False
    if not veranstaltung.art_veranstaltung == salonart:
        return False

    if not veranstaltung.ob_aktiv('livestream'):
        return False

    if veranstaltung.ist_zukunft() and not veranstaltung.ist_bald(60):
        return False

    return veranstaltung.ob_gekauft_von(kunde, 'livestream') or veranstaltung.ob_gekauft_von(kunde, 'aufzeichnung')



# für pdb tag
import pdb as pdb_module

from django.template import Node

class PdbNode(Node):

    def render(self, context):
        pdb_module.set_trace()
        return ''

@register.tag
def pdb(parser, token):
    return PdbNode()

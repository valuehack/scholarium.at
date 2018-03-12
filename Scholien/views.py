from django.http import HttpResponseRedirect
from Grundgeruest.views import DetailMitMenue, ListeMitMenue, TemplateMitMenue
from seite.settings import BASE_DIR, MEDIA_ROOT
from Grundgeruest.models import Nutzer
from . import models

from django.db import transaction
import sqlite3 as lite

from django.conf import settings
import os

from django.shortcuts import render
from Scholien.models import Artikel
from datetime import date


def liste_artikel(request):

    slug = request.GET.get('q')
    if slug:
        return ein_artikel(request, slug)

    # Introduction for non-members
    if not request.user.is_authenticated():
        return TemplateMitMenue.as_view(
            template_name='Gast/scholien.html',
            url_hier='/scholien',
            )(request)

    # Articles without publication date
    art_null = Artikel.objects.filter(datum_publizieren__isnull=True)
    # Articles that have been published
    art_pub = Artikel.objects.filter(datum_publizieren__isnull=False, datum_publizieren__lte=date.today())
    art_pub = art_pub.order_by('-datum_publizieren')
    # Articles that will be published on a specific date
    art_fut = Artikel.objects.filter(datum_publizieren__gt=date.today())
    art_fut = art_fut.order_by('-datum_publizieren')

    context = {
        'art_null': art_null,
        'art_pub': art_pub,
        'art_fut': art_fut,
    }
    return render(request, 'Scholien/artikel.html', context)


def liste_buechlein(request):
    if request.user.is_authenticated() and request.user.hat_guthaben():
        return ListeMitMenue.as_view(
            model=models.Buechlein,
            template_name='Scholien/liste_buechlein.html',
            context_object_name='buechlein',
            paginate_by=5)(request, page=request.GET.get('seite'))
    else:
        # im Template wird Kleinigkeit unterschieden:
        return TemplateMitMenue.as_view(
            template_name='Gast/scholien.html',
            )(request)


def ein_artikel(request, slug):
    return DetailMitMenue.as_view(
        template_name='Scholien/detail.html',
        model=models.Artikel,
        context_object_name='scholie')(request, slug=slug)


def ein_buechlein(request, slug):
    return DetailMitMenue.as_view(
        template_name='Scholien/detail_buechlein.html',
        model=models.Buechlein,
        context_object_name='scholienbuechlein')(request, slug=slug)


def daten_einlesen(request):
    aus_alter_db_einlesen()
    return HttpResponseRedirect('/scholien')


def pdfs_etc_einlesen():
    liste = models.Buechlein.objects.all()[2:4]
    namen = [b.slug+ext for b in liste for ext in ['.pdf', '.mobi', '.epub']]
    with open(os.path.join(BASE_DIR, 'hey'), 'w') as f:
        f.write('\n'.join(namen))

    os.system(("rsync -a --files-from=" + os.path.join(BASE_DIR, 'hey') +
               " wertewirt@scholarium.at:~/html/production/down_secure/" +
               "content_secure/ " + os.path.join(MEDIA_ROOT, 'scholienbuechlein')))

    os.system("rm " + os.path.join(BASE_DIR, 'hey'))

    # Dateinamen ändern, damit nicht ratbar
    neue_namen = {}
    for name in namen:
        von = os.path.join(MEDIA_ROOT, 'scholienbuechlein', name)
        n, ext = os.path.splitext(name)
        neu = n + '_' + Nutzer.erzeuge_zufall(8, 2) + ext
        neue_namen.update([(name, neu)])
        nach = os.path.join(MEDIA_ROOT, 'scholienbuechlein', neu)
        os.system("mv {} {}".format(von, nach))

    for b in liste:
        b.pdf.name = 'scholienbuechlein/' + neue_namen[b.slug+'.pdf']
        b.mobi.name = 'scholienbuechlein/' + neue_namen[b.slug+'.mobi']
        b.epub.name = 'scholienbuechlein/' + neue_namen[b.slug+'.epub']
        bild = b.slug + '.jpg'
        b.bild_holen('http://www.scholarium.at/schriften/'+bild, bild)
        b.save()


def aus_alter_db_einlesen():
    """ liest scholienartikel aus alter db (als
    .sqlite exportiert) aus
    !! Achtung, löscht davor die aktuellen Einträge !! """

    # Artikel auslesen
    models.Artikel.objects.all().delete()

    con = lite.connect(os.path.join(settings.BASE_DIR, 'alte_db.sqlite3'))
    with con:
        con.row_factory = lite.Row
        cur = con.cursor()
        cur.execute("SELECT * FROM blog;")

        zeilen = [dict(zeile) for zeile in cur.fetchall()]

    with transaction.atomic():
        for scholie in zeilen:
            if scholie['publ_date'] == '0000-00-00':
                scholie['publ_date'] = '1111-01-01'
            models.Artikel.objects.create(
                bezeichnung=scholie['title'],
                inhalt=scholie['public_text'],
                inhalt_nur_fuer_angemeldet=scholie['private_text'],
                datum_publizieren=scholie['publ_date'],
                slug=scholie['id'])

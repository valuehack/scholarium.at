import codecs
import re
import pypandoc
import os
from trello import TrelloClient
from slugify import slugify
import datetime
import requests

from django.urls import reverse
from django.conf import settings
from django.db import IntegrityError
from django.contrib.sites.models import Site

base_dir = os.path.join(settings.MEDIA_ROOT, 'Schriften')
bib = os.path.join(base_dir, "scholarium.bib")
md_path = os.path.join(base_dir, "Markdown")
html_path = os.path.join(base_dir, "HTML")


def buffer(scholie):
    try:
        link = 'https://%s%s' % (Site.objects.get(pk=settings.SITE_ID).domain,
                                 reverse('Scholien:artikel_detail', args=[scholie.slug]))
        data = [
            ('access_token', settings.BUFFER_ACCESS_TOKEN),
            ('text', 'Neue Scholie:'),
            ('media[link]', link)
        ]
        ids = [('profile_ids[]', id) for id in settings.BUFFER_SITE_IDS]
        payload = ids + data

        r = requests.post('https://api.bufferapp.com/1/updates/create.json', data=payload)
    except AttributeError:
        return 'Buffer values missing in settings.'
    return 'Buffer response: %s' % r


def markdown_to_html(markdown):
    # codecs.decode(markdown)
    text = "---\nbibliography: {}\n---\n\n{}\n\n## Literatur".format(bib, markdown)

    # to html
    md = text
    extra_args = []
    filters = ['pandoc-citeproc']
    html = pypandoc.convert(md, 'html', format='md', extra_args=extra_args, filters=filters)

    # blockquotes mit class versehen
    p = re.compile("<blockquote>")
    html = p.sub("<blockquote class=\"blockquote\">", html)

    # Gedankenstriche ("--" nach "–")
    p = re.compile("--")
    html = p.sub("&ndash;", html)

    # Literaturverzeichnis
    p = re.compile(r'<h2.*Literatur</h2>')
    split = re.split(p, html)
    literatur = split[1].lstrip() if len(split) > 1 else ""
    if not literatur:
        print('Keine Literatur gefunden.')

    # Trennungszeichen
    p = re.compile(r"<p>&lt;&lt;&lt;</p>")
    split = re.split(p, split[0])
    public = split[0]

    # lstrip entfernt mögliche Absätze am Anfang.
    private = split[1].lstrip() if len(split) > 1 else ""
    public2 = split[2].lstrip() if len(split) > 2 else ""
    if not private:
        print('Keinen privaten Teil gefunden.')
    return public, private, public2, literatur


# TODO: Beide Funktionen zusammenfassen.
def trelloToSQL():
    '''
    Liest Trello-Karten aus Liste "Texte lektoriert" des "Play-Boards" aus
    und wandelt Sie mit Pandoc in html um. Inklusive Literaturverzeichnis.
    Zusätzlich werden ein paar weitere Formatierungen vorgenommen.
    Das Ergebnis wird dann in die Datenbank geschrieben.
    Die Trello-Karten werden hinterher verschoben.
    '''
    from Scholien.models import Artikel

    client = TrelloClient(api_key=settings.TRELLO_API_KEY, token=settings.TRELLO_TOKEN)
    play_board = client.get_board('55d5dfee98d40fcb68fc0e0b')
    played_board = client.get_board('55c4665a4afe2f058bd3cb0a')
    target_list = played_board.get_list('5774e15c515d20dd2aa0b534')

    for list in play_board.open_lists():
        if list.name == "Texte lektoriert":
            print('%d lektorierte(n) Text(e) gefunden.' % len(list.list_cards()))
            # Karten werden von unten nach oben abgearbeitet.
            for card in list.list_cards()[::-1]:
                title = card.name
                text = card.desc
                fobj_out = codecs.open(os.path.join(md_path, "%s.md" % title), "w", "utf-8")
                # meta = codecs.open("%s" %meta,"r","utf-8")
                # fobj_out.write(meta.read())

                # ids
                p = re.compile(r"§§.*")
                id = p.findall(text)
                id = id[0][2:] if id else title
                priority = 1 if id[0] == '!' else 0
                id = slugify(id)
                text = p.sub("", text, count=1)

                fobj_out.write("---\nbibliography: {}\n---\n\n{}\n\n## Literatur".format(bib, text))
                fobj_out.close

                # to html
                fobj_out = codecs.open(os.path.join(md_path, "%s.md" % title), "r", "utf-8")
                md = fobj_out.read()
                extra_args = []
                filters = ['pandoc-citeproc']
                html = pypandoc.convert(md, 'html', format='md',  extra_args=extra_args, filters=filters)

                # blockquotes mit class versehen
                p = re.compile("<blockquote>")
                html = p.sub("<blockquote class=\"blockquote\">", html)

                # Gedankenstriche ("--" nach "–")
                p = re.compile("--")
                html = p.sub("&ndash;", html)

                # Trennungszeichen
                p = re.compile(r"<p>&lt;&lt;&lt;</p>")
                split = re.split(p, html)
                public = split[0]
                # lstrip entfernt mögliche Absätze am Anfang.
                private = split[1].lstrip() if len(split) > 1 else ""
                if not private:
                    print('Keinen privaten Teil gefunden für', title)
                    # print(html)

                try:
                    art_neu = Artikel.objects.create(
                        slug=id, bezeichnung=title, inhalt=public,
                        inhalt_nur_fuer_angemeldet=private, prioritaet=priority
                    )  # *art_neu* currently not in use
                    print('%s erfolgreich in DB übertragen.' % title)
                except IntegrityError as e:
                    print('Artikel schon vorhanden')
                except Exception as e:
                    print(title, 'failed:', e)
                    continue

                card.change_board(played_board.id, target_list.id)
                card.set_pos('top')


def publish():
    '''
    Neuer Post alle 6 Tage. Nach Priorität sortieren.
    '''
    from Scholien.models import Artikel

    artikel_pub = Artikel.objects.all().order_by('-datum_publizieren')
    last = (datetime.date.today() - artikel_pub[0].datum_publizieren).days
    message = ''

    # Check, ob Beitrag in letzten Tagen
    if last >= settings.RELEASE_PERIOD:
        artikel_p = Artikel.objects.filter(datum_publizieren=None, prioritaet=True)
        artikel_np = Artikel.objects.filter(datum_publizieren=None)

        # Check, ob Artikel mit Priorität vorhanden ist.
        if artikel_p:
            neu = artikel_p[0]
        elif artikel_np:
            message = 'Kein Artikel mit Priorität gefunden.'
            neu = artikel_np[0]
        else:
            message = 'Kein neuen Artikel gefunden.'

        if neu:
            neu.datum_publizieren = datetime.date.today()
            neu.save()
            r = buffer(neu)
            message = '%s publiziert. %s' % (neu, r)
    else:
        message = 'Letzter Artikel bereits vor %d Tagen veröffentlicht.' % last

    return message

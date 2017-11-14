# import mysql.connector
import codecs
import re
import pypandoc
import os
# import subprocess
from trello import TrelloClient
from slugify import slugify
import datetime
# from db_connector import Connector

from Scholien.models import Artikel
from django.conf import settings

base_dir = os.path.join(settings.MEDIA_ROOT, 'Schriften')
bib = os.path.join(base_dir,"scholarium.bib")
md_path = os.path.join(base_dir,"Markdown")
html_path = os.path.join(base_dir,"HTML")


def trelloToSQL():
    '''
    Liest Trello-Karten aus Liste "Texte lektoriert" des "Play-Boards" aus
    und wandelt Sie mit Pandoc in html um. Inklusive Literaturverzeichnis.
    Zusätzlich werden ein paar weitere Formatierungen vorgenommen.
    Das Ergebnis wird dann in die Datenbank geschrieben.
    Die Trello-Karten werden hinterher verschoben.
    '''

    #Trello Connection
    # with open(os.path.join(base_dir, 'trello.key'), 'r') as f:
    #     lines = f.readlines()
    #     client = TrelloClient(
    #         api_key=lines[0].strip(),
    #         # api_secret=lines[1].strip(),
    #         token=lines[1].strip(),
    #         # token_secret=lines[3].strip()
    #     )

    client = TrelloClient(api_key=settings.TRELLO_API_KEY, token=settings.TRELLO_TOKEN)
    play_board=client.get_board('55d5dfee98d40fcb68fc0e0b')
    played_board=client.get_board('55c4665a4afe2f058bd3cb0a')
    target_list=played_board.get_list('5774e15c515d20dd2aa0b534')

    for list in play_board.open_lists():
        if list.name=="Texte lektoriert":
            print('%d lektorierte(n) Text(e) gefunden.' % len(list.list_cards()))
            # Karten werden von unten nach oben abgearbeitet.
            for card in list.list_cards()[::-1]:
                title=card.name
                text=card.desc
                fobj_out = codecs.open(os.path.join(md_path, "%s.md" % title),"w","utf-8")
                #meta = codecs.open("%s" %meta,"r","utf-8")
                #fobj_out.write(meta.read())

                #ids
                p = re.compile(r"§§.*")
                id = p.findall(text)
                id = id[0][2:] if id else title
                priority = 1 if id[0] == '!' else 0
                id = slugify(id)
                text = p.sub("",text, count=1)

                fobj_out.write("---\nbibliography: {}\n---\n\n{}\n\n## Literatur".format(bib, text))
                fobj_out.close

                #to html
                fobj_out = codecs.open(os.path.join(md_path, "%s.md" % title),"r","utf-8")
                md=fobj_out.read()
                extra_args=[]
                filters=['pandoc-citeproc']
                html=pypandoc.convert(md, 'html', format='md',  extra_args=extra_args, filters=filters)

                #blockquotes mit class versehen
                p=re.compile("<blockquote>")
                html=p.sub("<blockquote class=\"blockquote\">",html)

                #Gedankenstriche ("--" nach "–")
                p=re.compile("--")
                html=p.sub("&ndash;",html)

                #Trennungszeichen
                p=re.compile(r"<p>&lt;&lt;&lt;</p>")
                split=re.split(p,html)
                public=split[0]
                # lstrip entfernt mögliche Absätze am Anfang.
                private=split[1].lstrip() if len(split) > 1 else ""
                if not private:
                    print('Keinen privaten Teil gefunden für',title)
                    # print(html)
                    
                try:
                    art_neu = Artikel.objects.create(slug=id, bezeichnung=title, inhalt=public, inhalt_nur_fuer_angemeldet=private, prioritaet=priority)
                except Exception as e:
                    print(title, 'failed:', e)
                    break
                    
                card.change_board(played_board.id, target_list.id)
                card.set_pos('top')
                print('%s erfolgreich in DB übertragen.' % title)
                
                
                
def druck(text = 'default'):
    print(text)

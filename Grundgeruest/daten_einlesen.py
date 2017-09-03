import os, shutil
from seite.settings import BASE_DIR, MEDIA_ROOT
from Grundgeruest.models import Nutzer
from Scholien.models import Buechlein

import pdb    
    
def buechlein_ebooks_einlesen():
    """ Kopiert die pdfs/epub/mobi der scholienbuechlein aus dem 
    input-Ordner nach media, verändert sicherheitshalber den Dateinamen, 
    und speichert den link in der db """
    liste = Buechlein.objects.all()
    buechlein = [(b.slug, b, [b.slug+ext for ext in ['.pdf', '.mobi', '.epub']]) for b in liste]
    
    os.chdir('/home/scholarium/')
    neue_namen = {}
    for slug, b, dreinamen in buechlein:
        for name in dreinamen:
            von = 'production/down_secure/content_secure/' + name
            n, ext = os.path.splitext(name)
            nachordner = os.path.join(MEDIA_ROOT, 'scholienbuechlein')
            dateifeld = getattr(b, ext)
            if dateifeld and dateifeld.name in os.listdir(nachordner):
                neue_namen.update([(name, dateifeld.name)])
                continue
            else:
                neu = n + '_' + Nutzer.erzeuge_zufall(8, 2) + ext
                neue_namen.update([(name, neu)])
                nach = nachordner + neu
                shutil.copy2(von, nach)
                dateifeld.name = 'scholienbuechlein/' + neu

        if not b.bild:
            bild = b.slug + '.jpg'
            b.bild_holen('http://www.scholarium.at/schriften/'+bild, bild)
        
        b.save()
        

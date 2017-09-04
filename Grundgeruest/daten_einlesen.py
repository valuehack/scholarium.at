import os, shutil
from seite.settings import BASE_DIR, MEDIA_ROOT
from Grundgeruest.models import Nutzer
from Scholien.models import Buechlein

import pdb    
    
def buechlein_ebooks_einlesen():
    """ Kopiert die pdfs/epub/mobi der scholienbuechlein aus dem 
    input-Ordner nach media, verändert sicherheitshalber den Dateinamen, 
    und speichert den link in der db """
    buechlein = Buechlein.objects.all()
    liste_ext = ['jpg', 'pdf', 'mobi', 'epub']
    
    os.chdir('/home/scholarium/production/')
    for b in buechlein:
        for ext in liste_ext:
            nachordner = os.path.join(MEDIA_ROOT, 'scholienbuechlein')
            dateifeld = b.bild if ext=='jpg' else getattr(b, ext)
            if dateifeld and dateifeld.name.split('/')[-1] in os.listdir(nachordner):
                continue
            else:
                von_ordner = 'schriften/' if ext=='jpg' else 'down_secure/content_secure/'
                von = '%s%s.%s' % (von_ordner, b.slug, ext)
                name_neu = '%s_%s.%s' % (b.slug, Nutzer.erzeuge_zufall(8, 2), ext)
                dateifeld.name = 'scholienbuechlein/%s' % name_neu
                shutil.copy2(von, os.path.join(MEDIA_ROOT, dateifeld.name))
                setattr(b, 'ob_' + ('bild' if ext=='jpg' else ext), True)

            b.save()


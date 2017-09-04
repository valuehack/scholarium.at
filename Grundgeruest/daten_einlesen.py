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
    buechlein = [(b, {ext: None for ext in ['pdf', 'mobi', 'epub']}) for b in liste]
    
    os.chdir('/home/scholarium/production/')
    for b, dreinamen in buechlein:
        for ext in dreinamen.keys():
            nachordner = os.path.join(MEDIA_ROOT, 'scholienbuechlein')
            dateifeld = getattr(b, ext)
            if dateifeld and dateifeld.name in os.listdir(nachordner):
                continue
            else:
                von = 'down_secure/content_secure/%s.%s' % (b.slug, ext)
                name_neu = '%s_%s.%s' % (b.slug, Nutzer.erzeuge_zufall(8, 2), ext)
                dateifeld.name = 'scholienbuechlein/%s' % name_neu
                shutil.copy2(von, os.path.join(MEDIA_ROOT, dateifeld.name)

        if not b.bild:
            bild = b.slug + '.jpg'
            b.bild_holen('http://www.scholarium.at/schriften/'+bild, bild)
        
        b.save()
        

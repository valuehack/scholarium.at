import os, shutil
from seite.settings import BASE_DIR, MEDIA_ROOT
from Grundgeruest.models import Nutzer
from Scholien.models import Buechlein

import pdb    
    
def buechlein_ebooks_einlesen():
    """ Kopiert die pdfs/epub/mobi der scholienbuechlein aus dem 
    input-Ordner nach media, verändert sicherheitshalber den Dateinamen, 
    und speichert den link in der db """
    liste = Buechlein.objects.all()[2:4]
    namen = [b.slug+ext for b in liste for ext in ['.pdf', '.mobi', '.epub']]
    
    os.chdir('/home/scholarium/')
    neue_namen = {}
    for name in namen:
        von = 'production/down_secure/content_secure/' + name
        n, ext = os.path.splitext(name)
        neu = n + '_' + Nutzer.erzeuge_zufall(8, 2) + ext
        neue_namen.update([(name, neu)])
        nach = os.path.join(MEDIA_ROOT, 'scholienbuechlein', neu)
        shutil.copy2(von, nach)

    for b in liste:
        b.pdf.name = 'scholienbuechlein/' + neue_namen[b.slug+'.pdf']    
        b.mobi.name = 'scholienbuechlein/' + neue_namen[b.slug+'.mobi']    
        b.epub.name = 'scholienbuechlein/' + neue_namen[b.slug+'.epub']    
        bild = b.slug + '.jpg'
        b.bild_holen('http://www.scholarium.at/schriften/'+bild, bild)
        b.save()
        

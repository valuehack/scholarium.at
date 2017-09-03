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
    #with open(os.path.join(BASE_DIR, 'hey'), 'w') as f:
    #    f.write('\n'.join(namen))
    
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
        #bild = b.slug + '.jpg'
        #b.bild_holen('http://www.scholarium.at/schriften/'+bild, bild)
        b.save()

        
    pdb.set_trace()
    return None
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

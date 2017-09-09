# -*- coding: utf-8 -*-
from django.shortcuts import get_object_or_404, render, redirect

from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.core.urlresolvers import reverse
from userena.models import UserenaSignup
from userena.mail import UserenaConfirmationMail
from userena.settings import USERENA_ACTIVATED
from django.views.generic import ListView, DetailView, TemplateView
from userena.utils import generate_sha1
from guardian.models import UserObjectPermission
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.contrib import messages

from django.db import transaction
import sqlite3 as lite
import os, pdb
from .models import *
from Scholien.models import Artikel
from Veranstaltungen.models import Veranstaltung
from Bibliothek.models import Buch
from .forms import ZahlungFormular, ProfilEditFormular
from datetime import date


def erstelle_liste_menue(user=None):
    if user is None or not user.is_authenticated():
        menue = GanzesMenue.objects.get(bezeichnung='Gast')
    else: # d.h. wenn nicht AnonymousUser zugreift
        return [
            ({'bezeichnung': 'Scholien', 'slug': 'scholien'}, [
            {'bezeichnung': 'Artikel', 'slug': 'scholien'},
            {'bezeichnung': 'Büchlein', 'slug': 'scholienbuechlein'}
            ]),
            ({'bezeichnung': 'Salons', 'slug': 'salons'}, [
            ]),
            ({'bezeichnung': 'Seminare', 'slug': 'seminare'}, [
            ]),
            ({'bezeichnung': 'Vortrag', 'slug': 'vortrag'}, [
            ]),
            ({'bezeichnung': 'Bücher', 'slug': 'buecher'}, [
            ]),
            ({'bezeichnung': 'Studium', 'slug': 'studium'}, [
            {'bezeichnung': 'Studium Generale', 'slug': 'studium/studium'},
            {'bezeichnung': 'craftprobe', 'slug': 'studium/craftprobe'},
            {'bezeichnung': 'Stipendium', 'slug': 'studium/baader-stipendium'},
            {'bezeichnung': 'Beratung', 'slug': 'studium/beratung'},
            ]),
        ]
    liste_punkte = []
    for punkt in menue.hauptpunkt_set.all():
        unterpunkte = punkt.unterpunkt_set.all
        liste_punkte.append((punkt, unterpunkte))
    return liste_punkte

def liste_menue_zurueckgeben(request):
    liste_punkte = erstelle_liste_menue(request.user)
    return {'liste_menue': liste_punkte}

class MenueMixin():
    from functools import partial
    extra_context = {}
    url_hier = '/'
    def get_context_data(self, **kwargs):
        liste_menue = erstelle_liste_menue(self.request.user)
        context = super().get_context_data(**kwargs)
        context['liste_menue'] = liste_menue
        context['url_hier'] = self.url_hier
        context.update(self.extra_context)
        return context
            

class TemplateMitMenue(MenueMixin, TemplateView):
    pass 
    
class ListeMitMenue(MenueMixin, ListView):
    pass

class DetailMitMenue(MenueMixin, DetailView):
    pass
        
def index(request):
    if request.user.is_authenticated():
        liste_artikel = Artikel.objects.order_by('-datum_publizieren')[:4]
        veranstaltungen = Veranstaltung.objects.order_by('-datum')[:3]
        medien = []
        mehr_buecher = Buch.objects.order_by('-zeit_erstellt')[:50]
        buecher = random.sample(list(mehr_buecher), 3)
        # Achtung, spam-message als Bsp., später rausnehmen 
        messages.info(request, 'Willkommen auf der Startseite')
        return TemplateMitMenue.as_view(
            template_name='startseite.html',
            extra_context={
                'liste_artikel': liste_artikel, 
                'medien': medien,
                'veranstaltungen': veranstaltungen,
                'buecher': buecher
            })(request)
    else:
        return TemplateMitMenue.as_view(
            template_name='Gast/startseite_gast.html'
            )(request)
    
def zahlen(request):
    # falls POST von unangemeldet, keine Fehlermeldungen:
    #if request.method=='POST' and 'von_spende' in request.POST:
    #    formular = ZahlungFormular(request.POST)
    
    # falls POST von hier, werden Daten verarbeitet:
    if request.method=='POST':
        # eine form erstellen, insb. um sie im Fehlerfall zu nutzen:
        formular = ZahlungFormular(request.POST)
        # und falls alle Eingaben gültig sind, Daten verarbeiten: 
        if formular.is_valid():
            nutzer = None
            if not (Nutzer.objects.filter(email=request.POST['email'])): #or request.user.is_authenticated()):
                # erstelle neuen Nutzer mit eingegebenen Daten:
                nutzer = Nutzer.neuen_erstellen(request.POST['email'])

            else:
                print('{0}gibts schon{0}'.format(10*'\n'))
                print(request.POST)
                nutzer = Nutzer.objects.get(email=request.POST['email'])
                
            profil = nutzer.my_profile
            nutzer.first_name = request.POST['vorname']
            nutzer.last_name = request.POST['nachname']
            
            
            profil.stufe = int(request.POST['stufe'])+1
            profil.guthaben_aufladen(request.POST['betrag'])
            # ? hier noch Zahlungsdatum eintragen, oden bei Eingang ?
            for attr in ['anrede', 'tel', 'firma', 'strasse', 'plz', 
                'ort', 'land']:
                setattr(profil, attr, request.POST[attr])

            nutzer.save()
            profil.save()
            
            # redirect to a new URL:
            return HttpResponseRedirect('/thanks/')
        
        if 'von_spende' in request.POST:
            formular = ZahlungFormular()
    
    # if a GET (or any other method) we'll create a blank form
    else:
        formular = ZahlungFormular()

    stufe = request.POST.get('stufe', 'Gast')
    betrag = request.POST.get('betrag', '75')

    context = {
        'formular': formular, 
        'betrag': betrag, 
        'stufe': stufe
    }
    
    return render(request, 'Produkte/zahlung.html', context)    


# profile_edit aus userena.views kopiert, um Initialisierung der Nutzer-Daten (Felder auf Nutzer heißen anders als userena erwartet) zu ändern
from userena.decorators import secure_required
from userena.utils import get_profile_model, get_user_model, get_user_profile
from guardian.decorators import permission_required_or_403
from userena import settings as userena_settings
from userena.views import ExtraContextTemplateView
from django.contrib import messages

@secure_required
@permission_required_or_403('change_profile', (get_profile_model(), 'user__username', 'username'))
def profile_edit(request, username, edit_profile_form=ProfilEditFormular,
                 template_name='userena/profile_form.html', success_url=None,
                 extra_context=None, **kwargs):
    """
    Edit profile.

    Edits a profile selected by the supplied username. First checks
    permissions if the user is allowed to edit this profile, if denied will
    show a 404. When the profile is successfully edited will redirect to
    ``success_url``.

    :param username:
        Username of the user which profile should be edited.

    :param edit_profile_form:

        Form that is used to edit the profile. The :func:`EditProfileForm.save`
        method of this form will be called when the form
        :func:`EditProfileForm.is_valid`.  Defaults to :class:`EditProfileForm`
        from userena.

    :param template_name:
        String of the template that is used to render this view. Defaults to
        ``userena/edit_profile_form.html``.

    :param success_url:
        Named URL which will be passed on to a django ``reverse`` function after
        the form is successfully saved. Defaults to the ``userena_detail`` url.

    :param extra_context:
        Dictionary containing variables that are passed on to the
        ``template_name`` template.  ``form`` key will always be the form used
        to edit the profile, and the ``profile`` key is always the edited
        profile.

    **Context**

    ``form``
        Form that is used to alter the profile.

    ``profile``
        Instance of the ``Profile`` that is edited.

    """
    user = get_object_or_404(get_user_model(), username__iexact=username)

    profile = get_user_profile(user=user)

    user_initial = {'vorname': user.first_name,
                    'nachname': user.last_name, 
                    'email': user.email,}

    form = edit_profile_form(instance=profile, initial=user_initial)

    if request.method == 'POST':
        form = edit_profile_form(request.POST, request.FILES, instance=profile,
                                 initial=user_initial)

        if form.is_valid():
            profile = form.save()

            if userena_settings.USERENA_USE_MESSAGES:
                messages.success(request, ('Ihr Profil wurde aktualisiert'),
                                 fail_silently=True)

            if success_url:
                # Send a signal that the profile has changed
                userena_signals.profile_change.send(sender=None,
                                                    user=user)
                redirect_to = success_url
            else: redirect_to = reverse('userena_profile_detail', kwargs={'username': username})
            return redirect(redirect_to)

    if not extra_context: extra_context = dict()
    extra_context['form'] = form
    extra_context['profile'] = profile
    return ExtraContextTemplateView.as_view(template_name=template_name,
                                            extra_context=extra_context)(request)
                                            
def profile_detail(request, username,
    template_name=userena_settings.USERENA_PROFILE_DETAIL_TEMPLATE,
    extra_context=None, **kwargs):
    return HttpResponseRedirect(reverse('userena_profile_edit', kwargs={'username': username}))


def seite_rest(request, slug):
    punkte = (Hauptpunkt.objects.filter(slug=slug) or 
              Unterpunkt.objects.filter(slug=slug))
    if not punkte: 
        raise Http404
    liste_menue = erstelle_liste_menue()
    return render(
        request, 
        'Grundgeruest/seite_test.html', 
        {'punkt': punkte[0], 'liste_menue': liste_menue})

def aus_datei_mitglieder_einlesen(request):
    """
    Liest Mitglieder aus der Datenbank im Parent-Ordner
    
    Idee: öffne Datenbank und hole Zeilen als dict Attribut -> Wert
    erstelle dict für alte Attributnamen -> neue Namen 
    erstelle Liste von Nutzern und speichere sie (wegen Profil und Signup)
    füge für jeden Nutzer alle Attribute hinzu, speichere
    """
    con = lite.connect(os.path.join(settings.BASE_DIR, 'alte_db.sqlite3'))
    with con:
        con.row_factory = lite.Row
        cur = con.cursor()
        cur.execute("SELECT * FROM mitgliederExt")

        zeilen = [dict(zeile) for zeile in cur.fetchall()]
            
    profil_attributnamen = dict([
        ('stufe', 'Mitgliedschaft'),
        ('anrede', 'Anrede'),
        ('tel', 'Telefon'),
        ('firma', 'Firma'),
        ('strasse', 'Strasse'),
        ('plz', 'PLZ'),
        ('ort', 'Ort'),
        ('land', 'Land'),
        ('guthaben', 'credits_left'),
        ('titel', 'Titel'),
        ('anredename', 'Anredename'),
        ('letzte_zahlung', 'Zahlung'),
        ('datum_ablauf', 'Ablauf'),
        ('alt_id', 'user_id'),
        ('alt_notiz', 'Notiz'),
        ('alt_scholien', 'Scholien'),
        ('alt_mahnstufe', 'Mahnstufe'),
        ('alt_auslaufend', 'auslaufend'),
        ('alt_gave_credits', 'gave_credits'),
        ('alt_registration_ip', 'user_registration_ip')
    ])

    nutzer_attributnamen = dict([
        ('email', 'user_email'),
        ('first_name', 'Vorname'),
        ('last_name', 'Nachname'),
        ('date_joined', 'user_registration_datetime'),
        ('last_login', 'last_login_time'),
    ])
    
    zeilen = zeilen[:]
    Nutzer.objects.filter(id__gt=3).delete()    
        
    letzte_id = max(Nutzer.objects.all().values_list('id', flat=True))
    
    liste_nutzer = []
    with transaction.atomic():
        for i, zeile in enumerate(zeilen):
            nutzer = Nutzer.leeren_anlegen()
            nutzer.username = 'alteDB_%s' % zeile['user_id']
            nutzer.is_active = True
            nutzer.save()
            print('alte id {} angelegt: {} vom {}'.format(
                zeile['user_id'], 
                zeile['user_email'], 
                zeile['user_registration_datetime']))
            liste_nutzer.append(nutzer)
    
    for zeile in zeilen: # falls None drin steht, gäbe es sonst Fehler
        zeile['Vorname'] = zeile['Vorname'] or ''
        zeile['Nachname'] = zeile['Nachname'] or ''
        for k, v in zeile.items():
            if v == '0000-00-00 00:00:00':
                zeile[k] = '1111-01-01 00:00:00'
            if v == '0000-00-00':
                zeile[k] = '1111-01-01'
        
    def eintragen_nutzer(nutzer, zeile):
        for neu, alt in nutzer_attributnamen.items():
            setattr(nutzer, neu, zeile[alt])

    def eintragen_profil(profil, zeile):
        for neu, alt in profil_attributnamen.items():
            setattr(profil, neu, zeile[alt])
    
    with transaction.atomic():
        for i, nutzer in enumerate(liste_nutzer):
            zeile = zeilen[i]
            eintragen_nutzer(nutzer, zeile)
            pw_alt = zeile['user_password_hash']
            nutzer.password = 'bcrypt$$2b$10${}'.format(pw_alt.split('$')[-1])
            nutzer.save()
            profil = nutzer.my_profile
            eintragen_profil(profil, zeile)
            profil.save()
    
    return 'fertig'

def aus_alter_db_einlesen():
    """ liest Mitwirkende aus alter db (als .sqlite exportiert) aus 
    !! Achtung, löscht davor die aktuellen Einträge !! """
    
    Mitwirkende.objects.all().delete()
    
    con = lite.connect(os.path.join(settings.BASE_DIR, 'alte_db.sqlite3'))
    with con:
        con.row_factory = lite.Row
        cur = con.cursor()
        cur.execute("SELECT * FROM crew;")

        zeilen = [dict(zeile) for zeile in cur.fetchall()]

    with transaction.atomic():
        for person in zeilen:
            neu = Mitwirkende.objects.create(alt_id=person['id'])
                
            for attr in ['name', 'text_de', 'text_en', 'link', 'level', 
                'start', 'end']:
                if person[attr] == '0000-00-00':
                    person[attr] = '1111-01-01'
                setattr(neu, attr, person[attr])
            
            neu.save()


def alles_aus_mysql_einlesen():
    """ Laedt newBig Datenbank runter und liest Daten ein (aktuelle Zeilen
    werden vorher geloescht) fuer:
     - Scholienartikel
     - Veranstaltungen
     - [zu vervollständigen]
    """
    import os 
    from Veranstaltungen.views import aus_alter_db_einlesen as einlesen_v
    from Scholien.views import aus_alter_db_einlesen as einlesen_s
    liste_dateien = os.listdir('.')
    if not 'alte_db.sql' in liste_dateien:
        print("ich will jetzt die newBig Datenbank runterladen...")
        os.system('mysqldump --extended-insert=FALSE --complete-insert=TRUE -h 37.148.204.116 -u newBig -p newBig > alte_db.sql')
        print('habe newBig nach alte_db.sql runtergeladen')
    if not 'alte_db.sqlite3' in liste_dateien:
        os.system('./mysql2sqlite alte_db.sql | sqlite3 alte_db.sqlite3')
        print('habe alte_db.sqlite3 erzeugt')
    if input('...werde jetzt Veranstaltungen und Medien löschen und aus alter DB übernehmen - richtig? Zum Abbrechen etwas eingeben, Fortfahren mit nur Eingabetaste'):
        print('abgebrochen')
    else:
        einlesen_v()
        print('eingelesen')
    if input('...werde jetzt Scholienartikel löschen und aus alter DB übernehmen - richtig? Zum Abbrechen etwas eingeben, Fortfahren mit nur Eingabetaste'):
        print('abgebrochen')
    else:
        einlesen_s()
        print('eingelesen')


def db_runterladen(request):
    from django.utils.encoding import smart_str
    import os
    from seite.settings import BASE_DIR
     
    with open(os.path.join(BASE_DIR, 'db.sqlite3'), 'rb') as datei:
        datenbank = datei.read()

    response = HttpResponse(datenbank, content_type='application/force-download') 
    response['Content-Disposition'] = 'attachment; filename="db.sqlite3"'
    
    return response

class ListeAktiveMitwirkende(ListeMitMenue):
    template_name='Gast/mitwirkende.html'
    context_object_name='mitwirkende'
    
    def get_queryset(self):
        return Mitwirkende.objects.exclude(end__lt=date.today())
    

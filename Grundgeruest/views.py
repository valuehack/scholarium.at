# -*- coding: utf-8 -*-
from django.shortcuts import get_object_or_404, render, redirect

from django.http import HttpResponseRedirect, HttpResponse, Http404, JsonResponse
from django.core.urlresolvers import reverse
from userena.models import UserenaSignup
from userena.mail import UserenaConfirmationMail
from userena.settings import USERENA_ACTIVATED
from django.views.generic import ListView, DetailView, TemplateView
from userena.utils import generate_sha1
from django.conf import settings
from guardian.models import UserObjectPermission
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.contrib import messages
from django.contrib.sites.models import Site

from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from userena.mail import send_mail as sendmail_von_userena

from django.db import transaction
import sqlite3 as lite
import os, pdb, ipdb, json
from .models import *
from Produkte.models import Spendenstufe, Kauf
from Scholien.models import Artikel
from Veranstaltungen.models import Veranstaltung
from Bibliothek.models import Buch
from .forms import ZahlungFormular, ProfilEditFormular
from datetime import date, timedelta, datetime
from django.core.mail import send_mail
import paypalrestsdk
import pprint, string
from django.views.decorators.csrf import csrf_exempt


class Nachricht():
    mailadresse = settings.DEFAULT_TO_EMAILS[0] # die von Georg
    @classmethod
    def nutzer_gezahlt(cls, nutzer_pk, betrag, zahlart):
        nutzer = Nutzer.objects.get(pk=nutzer_pk)
        text = '''Hallo Georg!

Ein Nutzer hat eine Unterstützung gezeichnet! Prüf' doch mal bei Gelegenheit, ob das Geld eingegangen ist.
 * Nutzer:
email: %s, id: %s, username: %s
 * Zahlung:
Betrag: %s, Zahlungsart: %s, aktuelle Zeit: %s
''' % (nutzer.email, nutzer_pk, nutzer.username, betrag, zahlart, str(datetime.now()).split('.')[0])
        send_mail(
            subject='[website] Nutzer hat gezahlt',
            message=text,
            from_email='iljasseite@googlemail.com',
            recipient_list=['ilja1988@googlemail.com', cls.mailadresse],
            fail_silently = False,
        )

        rHerr = 'r Herr' if nutzer.my_profile.anrede=='Herr' else ' Frau'
        subject = 'Herzlich willkommen'
        message_plain = None
        message_html = render_to_string(
            'Grundgeruest/email/dank_unterstuetzung.html', {
            'betrag': betrag, 
            'datum': str(datetime.now()).split('.')[0],
            'nachname': nutzer.last_name,
            'rHerr': rHerr,
            'pk': nutzer.pk, 
            'zahlart': zahlart,
            'host': settings.HOSTNAME,
        })
        email_from = settings.DEFAULT_FROM_EMAIL
        email_to = [nutzer.email]
        sendmail_von_userena(subject, message_plain, message_html, email_from, email_to,
              custom_headers={}, attachments=())


    @classmethod
    def bestellung_versenden(cls, request):
        nutzer = request.user
        from Produkte.views import Warenkorb
        text_warenkorb = ''
        for pk, ware in Warenkorb(request).items.items():
            text_warenkorb += "%s x %s\n" % (ware.quantity, Kauf.obj_aus_pk(pk))
        text = '''Hallo Georg!

Ein Nutzer hat Waren zum Versand bestellt.

Adresse:
%s
eMail für Rückfragen:
%s

Waren:
%s
''' % (nutzer.my_profile.adresse_ausgeben(), request.user.email, text_warenkorb)
        send_mail(
            subject='[website] Bestellung zum Versand eingegangen',
            message=text,
            from_email='iljasseite@googlemail.com',
            recipient_list=['ilja1988@googlemail.com', cls.mailadresse],
            fail_silently = False,
        )

    @classmethod
    def studiumdings_gebucht(cls, request):
        nutzer = request.user
        from Produkte.views import Warenkorb
        text_warenkorb = ''
        for pk, ware in Warenkorb(request).items.items():
            text_warenkorb += "%s x %s\n" % (ware.quantity, Kauf.obj_aus_pk(pk))
        text = '''Hallo Georg!

Ein Nutzer hat Studiendinger gebucht.

Waren:
%s

Vermutlich muss er eine händische Mail zur weiteren Vorgehensweise bekommen:
%s

''' % (text_warenkorb, request.user.email)
        send_mail(
            subject='[website] Bestellung Studiendinger eingegangen',
            message=text,
            from_email='iljasseite@googlemail.com',
            recipient_list=['ilja1988@googlemail.com', cls.mailadresse],
            fail_silently = False,
        )

    @classmethod
    def teilnahme_gebucht(cls, request):
        nutzer = request.user
        from Produkte.views import Warenkorb
        text_warenkorb = ''
        for pk, ware in Warenkorb(request).items.items():
            text_warenkorb += "%s x %s\n" % (ware.quantity, Kauf.obj_aus_pk(pk))
        text = '''Hallo Georg!

Ein Nutzer hat Teilnahmen an kommenden Veranstaltungen gebucht.

Waren:
%s

Mailadresse für eventuelle Rückfragen:
%s

''' % (text_warenkorb, request.user.email)
        send_mail(
            subject='[website] Bestellung Teilnahmen eingegangen',
            message=text,
            from_email='iljasseite@googlemail.com',
            recipient_list=['ilja1988@googlemail.com', cls.mailadresse],
            fail_silently = False,
        )


def erstelle_liste_menue(user=None):
    if user is None or not user.is_authenticated() or user.my_profile.get_Status()[0] == 0:
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
            {'bezeichnung': 'Stipendium', 'slug': 'studium/baader-stipendium'},
            {'bezeichnung': 'Beratung', 'slug': 'studium/beratung'},
            {'bezeichnung': 'Orientierungscoaching', 'slug': 'studium/orientierungscoaching'},
            ]),
        ]
    liste_punkte = []
    for punkt in menue.hauptpunkt_set.all():
        unterpunkte = punkt.unterpunkt_set.all
        liste_punkte.append((punkt, unterpunkte))
    return liste_punkte

def liste_menue_zurueckgeben(request):
    """ context-processor """
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
        alle_veranstaltungen = Veranstaltung.objects.order_by('datum')
        veranstaltungen = [v for v in alle_veranstaltungen if v.ist_zukunft()][-3:]
        medien = [v for v in alle_veranstaltungen if v.ob_aufzeichnung][-3:]
        mehr_buecher = Buch.objects.order_by('-zeit_erstellt')[:50]
        buecher = random.sample(list(mehr_buecher), 3)
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


def paypal_bestaetigung(request):
    #from Grundgeruest.paypal import anfrage_token, fuehre_payment_aus, pruefe_payment
    #access_token = anfrage_token()
    #zahlung = pruefe_payment(request.GET.get('paymentID'), access_token)
    # (der 'state' der Antwort wird nicht genutzt, da wir kein reproduzierbares Muster gefunden haben)

    paypalrestsdk.configure({
        "mode": settings.PAYPAL_MODE,
        "client_id": settings.PAYPAL_CLIENT_ID,
        "client_secret": settings.PAYPAL_CLIENT_SECRET })

    if 'paymentID' in request.GET:
        payment = paypalrestsdk.Payment.find(request.GET['paymentID'])
        pprint.pprint(payment)
        if payment.state == 'approved':
            betrag = int(float(payment.to_dict()['transactions'][0]['amount']['total']))
            stufe = Spendenstufe.objects.get(spendenbeitrag=betrag).pk
            if request.user.is_authenticated:
                pk=request.user.pk
                email=request.user.email
            else:
                pk=request.session['neuer_nutzer_pk']
                email = Nutzer.objects.get(pk=pk).email
            datendict = {'betrag': betrag, 'stufe': stufe, 'email': email}
            upgrade_nutzer(request, datendict)
            Nachricht.nutzer_gezahlt(pk, betrag, 'PayPal')

            return HttpResponseRedirect("/spende/zahlung/")
            #messages.error(request, 'Transaktion nicht bestätigt.')
            #return JsonResponse({"Status der paypal-Zahlung": "nicht erfolgreich"})

def upgrade_nutzer(request, datendict):
    ''' Setzt die neue Unterstützerstufe nach erfolgreicher Zahlung.'''
    # FIXME: Höhere Stufe kann durch kleinere verlängert werden! Unterstützungsmodel implementieren stattdesssen!
    if request.user.is_authenticated():
        nutzer = request.user
    else:
        nutzer = Nutzer.objects.get(email=datendict['email'])
    if nutzer.my_profile.stufe < int(datendict['stufe']):
        nutzer.my_profile.stufe = int(datendict['stufe'])
    nutzer.my_profile.guthaben_aufladen(int(datendict['betrag']))
    today = datetime.now().date()
    nutzer.my_profile.letzte_zahlung = today
    nutzer.my_profile.datum_ablauf = today + timedelta(days=365)
    nutzer.my_profile.save()
    messages.success(request, 'Vielen Dank für Ihre Unterstützung!')
    return HttpResponseRedirect(reverse('Grundgeruest:index'))

def zahlen(request):
    def formular_init():
        if request.user.is_authenticated():
            formular = ZahlungFormular(instance=request.user.my_profile,
                    initial = {'vorname': request.user.first_name,
                               'nachname': request.user.last_name,
                               'email': request.user.email})
            return formular
        else:
            return ZahlungFormular()

    def nutzerdaten_speichern():
        """ Speichert Profildaten, alles was nix mit der Zahlung zu tun
        hat; Zahlung erst bei der nächsten Bestätigung eintragen
        Nutzer wird ausgegeben für später; falls der neu erstellte Nutzer
        noch nicht eingeloggt ist, muss man ihn """
        if request.user.is_authenticated():
            nutzer = request.user
            #if request.post['email'] != nutzer.email:
            #    messages.warning(request, 'ihre emailadresse konnte nicht geändert werden. bitte nutzen sie das formular auf der profilseite unten.')
        elif not (Nutzer.objects.filter(email=request.POST['email'])):
            # erstelle neuen nutzer mit eingegebenen daten:
            nutzer = Nutzer.neuen_erstellen(request.POST['email'])
            request.session['neuer_nutzer_pk'] = nutzer.pk
        else:
            messages.warning(request, 'Wir kennen Sie schon. Bitte loggen Sie sich zur Sicherheit ein, um Ihre Daten bearbeiten und Unerstützungen eintragen.')
            return 'zu_login'

        profil = nutzer.my_profile
        nutzer.first_name = request.POST['vorname']
        nutzer.last_name = request.POST['nachname']
        for attr in ['anrede', 'tel', 'firma', 'strasse', 'plz', 'ort', 'land']:
            setattr(profil, attr, request.POST[attr])

        nutzer.save()
        profil.save()
        return nutzer

    def nutzer_upgrade():
        return upgrade_nutzer(request, request.POST)

    formular = formular_init()
    context = {}

    if request.method == 'POST':
        pprint.pprint(request.POST)

        if 'von_spende' in request.POST: # falls POST von unangemeldet, keine Fehlermeldungen:
            pass # TODO: Übertragen, von wo User gekommen sind
        elif 'state' in request.POST:
            return nutzer_upgrade()
        elif 'bestaetigung' in request.POST:
            Nachricht.nutzer_gezahlt(Nutzer.objects.get(email=request.POST['email']).pk, request.POST['betrag'], {'b': 'Bar', 'u': 'Überweisung'}[request.POST['zahlungsweise']])
            return nutzer_upgrade()
        else: # dann POST von hier, also Daten verarbeiten:
            formular = ZahlungFormular(request.POST)
            # und falls alle Eingaben gültig sind, Daten verarbeiten:
            if formular.is_valid():
                if nutzerdaten_speichern() == 'zu_login': # dann gibt's redirect, sonst wird schlicht gespeichert
                    return HttpResponseRedirect('/nutzer/anmelden/?next=/spende/zahlung/')
                if request.POST['zahlungsweise']=='p':
                    context.update({'sichtbar': True})
                else:
                    return zahlungsabwicklung_rest(request, formular)
            else:
                print('Bitte korrigieren Sie die Fehler im Formular')
                messages.error(request, 'Formular ungültig.')

    # ob's GET war oder vor_spende, suche Daten um auf sich selbst zu POSTen
    if request.user.is_authenticated:
        default_stufe = request.user.my_profile.stufe or 1 # also 1 falls sie 0 war
    else:
        default_stufe = 1
    default_betrag = Spendenstufe.objects.get(pk=default_stufe).spendenbeitrag
    stufe = request.POST.get('stufe', default_stufe)
    betrag = request.POST.get('betrag', default_betrag)

    context.update({
        'formular': formular,
        'betrag': betrag,
        'stufe': stufe,
        'paypal_mode': "production",
        'paypal_id': settings.PAYPAL_CLIENT_ID,
    })

    return render(request, 'Produkte/zahlung.html', context)


def zahlungsabwicklung_paypal(request):
    pass

def zahlungsabwicklung_rest(request, formular):
    context = {
        'nutzer': Nutzer.objects.get(email=request.POST['email']),
        'formular': formular
    }
    return render(request, 'Produkte/zahlung_bestaetigen.html', context)


class paypal_von_merlin():

    def getWebProfile():
        # Gets Paypal Web Profile
        wpn = ''.join(random.choice(string.ascii_uppercase) for i in range(12))

        web_profile = paypalrestsdk.WebProfile({
        "name": wpn,
        # "temporary": "true",
        "presentation": {
            "brand_name": "scholarium",
            "logo_image": "https://drive.google.com/open?id=0B4pA_9bw5MghZEVuQmJGaS1FSFU",
            "locale_code": "AT"
        },
        "input_fields": {
            "allow_note": True,
            "no_shipping": 1,
            "address_override": 1
        },
        "flow_config": {
            "landing_page_type": "login",
            "bank_txn_pending_url": 'http://' + Site.objects.get(pk=settings.SITE_ID).domain + reverse('gast_zahlung'),
            "user_action": "commit"
        }})

        if web_profile.create():
            print("Web Profile[%s] created successfully" % (web_profile.id))
            return web_profile
        else:
            print(web_profile.error)
            return None


    def paypalZahlungErstellen(stufe):
        payment = paypalrestsdk.Payment({
            "intent": "sale",
            "experience_profile_id": web_profile.id,
            "payer": {
                "payment_method": "paypal"},
            "redirect_urls": {
                "return_url": 'http://' + Site.objects.get(pk=settings.SITE_ID).domain + reverse('gast_zahlung'), # TODO: Alte POST Daten(Ausgewählte Stufe) wieder übergeben.
                "cancel_url": 'http://' + Site.objects.get(pk=settings.SITE_ID).domain + reverse('gast_spende')},
            # "note_to_payer": "Bei Fragen wenden Sie sich bitte an info@scholarium.at.",
            "transactions": [{
                "payee": {
                    "email": "info@scholarium.at",
                    "payee_display_metadata": {
                        "brand_name": "scholarium"}},
                "item_list": {
                    "items": [{
                        "name": str(stufe),
                        "sku": stufe.id,
                        "price": request.POST['betrag'],
                        "currency": "EUR",
                        "quantity": 1}]},
                "amount": {
                    "total": request.POST['betrag'],
                    "currency": "EUR"},
                "description": stufe.beschreibung}]})

        if payment.create():
            print("Payment[%s] created successfully" % (payment.id))
            pprint.pprint(payment)
            return payment
        else:
          print(payment.error)
          return None

    def weiterleiten_zu_confirm():
        paypalrestsdk.configure({
            "mode": settings.PAYPAL_MODE,
            "client_id": settings.PAYPAL_CLIENT_ID,
            "client_secret": settings.PAYPAL_CLIENT_SECRET })

        web_profile = getWebProfile()
        payment = paypalZahlungErstellen(stufe)

        # Redirect the user to given approval url
        approval_url = next((p.href for p in payment.links if p.rel == 'approval_url'))
        return HttpResponseRedirect(approval_url)

    def empfage_user_nach_approval():
        if request.GET.get('paymentId'):
            payment = paypalrestsdk.Payment.find(request.GET['paymentId'])
            pprint.pprint(payment)
            if payment.state == 'approved':
                if payment.execute({"payer_id": request.GET['PayerID']}):
                    print("Payment executed successfully")
                    nutzerErstellen()
                    messages.success(request, ('Herzlichen Glückwunsch, Sie sind nun %s' % payment.item))
                    HttpResponseRedirect(reverse('Grundgeruest:index'))
                    print(payment.error)
            else:
                pass
                messages.error(request, 'Transaktion nicht bestätigt.')



# profile_edit aus userena.views kopiert, um Initialisierung der Nutzer-Daten (Felder auf Nutzer heißen anders als userena erwartet) zu ändern
from userena.decorators import secure_required
from userena.utils import get_profile_model, get_user_model, get_user_profile
from guardian.decorators import permission_required_or_403
from userena import settings as userena_settings
from userena.views import ExtraContextTemplateView
from django.contrib import messages
from userena.views import signin


def anmelden(request, *args, **kwargs):
    '''
    Zeigt nach erfolgreicher Anmeldung definierte Meldungen an.
    '''
    s = signin(request, *args, **kwargs)
    if request.user.is_authenticated():
        if request.user.my_profile.get_Status()[0] == 1:
            messages.error(request, 'Ihre Unterstützung ist abgelaufen. Um wieder Zugang zu den Inhalten zu erhalten, erneuern Sie diese bitte - <a href="/spende/zahlung">Unterstützung erneuern!</a>', extra_tags="safe")
        if request.user.my_profile.get_Status()[0] == 2:
            messages.error(request, 'Ihre Unterstützung läuft in weniger als 30 Tagen ab - <a href="/spende/zahlung">Unterstützung erneuern!</a>', extra_tags="safe")
    return s


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

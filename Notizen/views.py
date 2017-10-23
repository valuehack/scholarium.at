from django.shortcuts import render
from django.core.urlresolvers import reverse
from django.views.generic.edit import CreateView
from . import models
from Veranstaltungen.models import Veranstaltung, ArtDerVeranstaltung
import ipdb


class ZeigenUndEintragen(CreateView):
    """ zeigt die bisher einzige Liste an """
    template_name = 'Notizen/liste.html'
    model = models.Zeile
    fields = ['text']
    context_object_name = 'liste'
    
    def get_success_url(self, *args, **kwargs):
        return reverse('aktueller_livestream')

    def render_to_response(self, context, **kwargs):
        """ Gibt eine Instanz von TemplateResponse zurück
        ich übergebe der zusätzlich eine Liste aller Zeilen; später nur die 
        zugehörigen zu einer models.Liste """
        response = super().render_to_response(context, **kwargs)
        # übergebe Salon und Liste von Zeilen
        if 'aktueller_salon' not in self.request.session:
            artsalon = ArtDerVeranstaltung.objects.get(bezeichnung='Salon')
            allesalons = Veranstaltung.objects.filter(art_veranstaltung=artsalon).order_by('-datum')
            salons = [s for s in allesalons if s.ob_livestream and not s.ist_vergangen()]
            if not salons:
                salon = None
            else:
                salon = salons[0]
            self.request.session['aktueller_salon'] = salon.pk
        else:
            salon = Veranstaltung.objects.get(pk=self.request.session['aktueller_salon'])
        
        if not salon:
            liste = None
        else:
            if models.Liste.objects.filter(salon=salon):
                liste = models.Liste.objects.get(salon=salon)
            else:
                liste = models.Liste.objects.create(salon=salon)

        response.context_data.update([
            ('salon', salon), 
            ('liste', models.Zeile.objects.filter(liste=liste))
        ])
        return response
        
    def form_valid(self, form):
        """ Setzt autor und liste für die Notizzeile.
        form.instance wurde vor dem Aufrufen davon erstellt, nur noch nicht
        in die db geschrieben (wär ja auch nicht valide); vorher müssen die 
        null=False-Felder gesetzt werden """
        form.instance.autor_id = self.request.user.pk or 1 # für Anonymous
        if 'aktueller_salon' in self.request.session:
            salon = Veranstaltung.objects.get(pk=self.request.session['aktueller_salon'])
            form.instance.liste_id = int(salon.liste.pk)
        form.instance.save()
        return super().form_valid(form)

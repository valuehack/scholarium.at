from django import forms
from userena.forms import SignupForm
from django.contrib.auth import get_user_model
from .models import ScholariumProfile#, MeinUserenaSignup
from userena.models import UserenaSignup # das ist Absicht, dass das und Mein~ importiert wird
from userena.models import UserenaSignup as MeinUserenaSignup # das ist Absicht, dass das und Mein~ importiert wird
from userena.utils import generate_sha1, get_profile_model
from django_countries.widgets import CountrySelectWidget

from django.utils.translation import ugettext_lazy as _
from collections import OrderedDict



class Anmeldeformular(SignupForm):
    """
    Kopiert aus SigninForm aus userena.forms, angepasst teils nach der Idee
    wie in SigninFormOnlyEmail gemacht    
    Habe die Länge und Erzeugungsart des autogenerierten Namens verlängert. 
    """
    def __init__(self, *args, **kwargs):
        super(Anmeldeformular, self).__init__(*args, **kwargs)
        del self.fields['username']
        del self.fields['password1']
        del self.fields['password2']

    def save(self):
        # erzeuge zufallsnamen, wie in SignupFormOnlyEmail
        Nutzer = get_user_model()
        new_user = Nutzer.neuen_erstellen(self.cleaned_data['email'])
        
        return new_user


class ProfilFormular(forms.ModelForm):
    """ Base form used for fields that are always required """
    first_name = forms.CharField(label=_('First name'),
                                 max_length=30,
                                 required=False)
    last_name = forms.CharField(label=_('Last name'),
                                max_length=30,
                                required=False)

    def __init__(self, *args, **kw):
        super(ProfilFormular, self).__init__(*args, **kw)
        # Put the first and last name at the top
        new_order = [('first_name', self.fields['first_name']),
                     ('last_name', self.fields['last_name'])]
        new_order.extend(list(self.fields.items())[:-2])
        self.fields = OrderedDict(new_order)

    class Meta:
        model = get_profile_model()
        exclude = ['user', 'guthaben', 'stufe']

    def save(self, force_insert=False, force_update=False, commit=True):
        profile = super(ProfilFormular, self).save(commit=commit)
        # Save first and last name
        user = profile.user
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.save()

        return profile


class ZahlungFormular(forms.ModelForm):
    email = forms.EmailField()
    vorname = forms.CharField()
    nachname = forms.CharField()
    zahlungsweise = forms.ChoiceField(
        widget=forms.RadioSelect,
        choices=[
            ('u', 'Überweisung'), 
            ('p', 'PayPal'), 
            ('b', 'Bar')
        ])
        
    class Meta:
        model = ScholariumProfile
        fields = ['email', 'anrede', 'vorname', 'nachname', 'tel', 'firma', 
            'strasse', 'plz', 'ort', 'zahlungsweise', 'land']
        widgets = {'land': CountrySelectWidget()}


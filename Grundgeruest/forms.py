from django import forms
from userena.forms import SignupForm
from django.contrib.auth import get_user_model
from .models import ScholariumProfile

from hashlib import sha1
import random

class Anmeldeformular(SignupForm):
    """
    Kopiert und angepasst aus SigninFormOnlyEmail aus userena.forms
    
    Habe die Länge des autogenerierten Namens verlängert. Man könnte anderes 
    Zeug
    """
    def __init__(self, *args, **kwargs):
        super(Anmeldeformular, self).__init__(*args, **kwargs)
        del self.fields['username']

    def save(self):
        """ Generate a random username before falling back to parent signup form """
        while True:
            username = sha1(str(random.random()).encode('utf-8')).hexdigest()[:20]
            try:
                get_user_model().objects.get(username__iexact=username)
            except get_user_model().DoesNotExist: break

        self.cleaned_data['username'] = username
        return super(Anmeldeformular, self).save()

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
            'strasse', 'plz', 'ort', 'zahlungsweise']

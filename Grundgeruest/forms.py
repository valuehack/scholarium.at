from django import forms
from userena.forms import SignupForm
from django.contrib.auth import get_user_model
from .models import ScholariumProfile
from django_countries.widgets import CountrySelectWidget


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


class ZahlungFormular(forms.ModelForm):
    payment_choices = [
        ('u', 'Überweisung'),
        ('p', 'PayPal'),
        ('b', 'Bar'),
    ]
    email = forms.EmailField()
    vorname = forms.CharField(required=False)
    nachname = forms.CharField(required=False)
    zahlungsweise = forms.ChoiceField(
        widget=forms.RadioSelect,
        choices=payment_choices)

    class Meta:
        model = ScholariumProfile
        fields = ['email', 'anrede', 'vorname', 'nachname', 'tel', 'firma',
                  'strasse', 'plz', 'ort', 'zahlungsweise', 'land']
        widgets = {'land': CountrySelectWidget()}


class ProfilEditFormular(forms.ModelForm):
    email = forms.EmailField(disabled=True)
    vorname = forms.CharField(required=False)
    nachname = forms.CharField(required=False)

    class Meta:
        model = ScholariumProfile
        fields = ['email', 'anrede', 'vorname', 'nachname', 'tel', 'firma',
                  'strasse', 'plz', 'ort', 'land']
        widgets = {'land': CountrySelectWidget()}

    def save(self, force_insert=False, force_update=False, commit=True):
        profile = super(ProfilEditFormular, self).save(commit=commit)
        # Save first and last name
        user = profile.user
        user.first_name = self.cleaned_data['vorname']
        user.last_name = self.cleaned_data['nachname']
        user.save()

        return profile

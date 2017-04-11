from django import forms
from Grundgeruest.models import ScholariumProfile

class ZahlungFormular(forms.ModelForm):
    email = forms.EmailField()
    vorname = forms.CharField()
    nachname = forms.CharField()
    zahlungsweise = forms.ChoiceField(
        choices=[
            ('u', 'Überweisung'), 
            ('p', 'PayPal'), 
            ('b', 'Bar')
        ])
        
    class Meta:
        model = ScholariumProfile
        fields = ['email', 'anrede', 'vorname', 'nachname', 'tel', 'firma', 
            'strasse', 'plz', 'ort', 'zahlungsweise']

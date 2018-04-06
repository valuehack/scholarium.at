from django import forms
from Grundgeruest.models import ScholariumProfile
from Produkte.models import Spendenstufe


class Rechnung2PdfForm(forms.Form):
    firm = forms.CharField(max_length=50, initial='scholarium')
    author = forms.CharField(max_length=50, initial='Georg A. Schabetsberger')
    recipent = forms.CharField(initial='''Max Mustermann
Holsteinische Str. 777
10717 Berlin
Deutschland''', widget=forms.Textarea)
    # ansprache = forms.CharField(initial='')
    # startnote = forms.CharField(initial='')

    description = forms.CharField(max_length=100, label='description')
    count = forms.IntegerField(label='count')
    price = forms.FloatField(label='price')
    details = forms.CharField(label='details')

    middlenote = forms.CharField(initial='Bitte überweisen Sie den Gesamtbetrag innerhalb von 14 Tagen, mit Angabe '
                                         'der Rechnungsnummer, auf folgendes Konto:',
                                 widget=forms.Textarea)

    Inhaber = forms.CharField(max_length=100, label='Inhaber', initial='scholarium')
    IBAN = forms.CharField(max_length=100, label='IBAN', initial='AT81 2011 1827 1589 8503')
    BIC = forms.CharField(max_length=100, label='BIC', initial='GIBAATWWXXX')

    # closingnote = forms.CharField(initial = 'Mit freundlichen Grüßen,')


class TrelloToSQLForm():
    pass


class CSVForm(forms.Form):
    fields = [
        ('anrede', 'Anrede'),
        ('first_name', 'Vorname'),
        ('last_name', 'Nachname'),
        ('email', 'Email'),
        ('strasse', 'Straße'),
        ('ort', 'Ort'),
        ('land', 'Land'),
        ('firma', 'Firma'),
        ('plz', 'Postleitzahl'),
    ]
    state_fields = [
        ('abgelaufen', 'abgelaufen'),
        ('aktiv', 'aktiv'),
    ]
    stufe_choices = [('0', 'Interessent')] + [(s.pk, s.bezeichnung) for s in Spendenstufe.objects.all()]

    values = forms.MultipleChoiceField(fields, widget=forms.CheckboxSelectMultiple)
    stufen = forms.MultipleChoiceField(stufe_choices, widget=forms.CheckboxSelectMultiple)
    states = forms.MultipleChoiceField(state_fields, widget=forms.CheckboxSelectMultiple)

from django import forms
from userena.forms import SignupForm
from django.contrib.auth import get_user_model
from .models import ScholariumProfile#, MeinUserenaSignup
from userena.models import UserenaSignup # das ist Absicht, dass das und Mein~ importiert wird
from userena.models import UserenaSignup as MeinUserenaSignup # das ist Absicht, dass das und Mein~ importiert wird
from userena.utils import generate_sha1

#from hashlib import sha1
#import random

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
        while True:
            username = Nutzer.erzeuge_username()
            try:
                get_user_model().objects.get(username__iexact=username)
            except get_user_model().DoesNotExist: break

        self.cleaned_data['username'] = username
        # fast aus SignupForm kopiert, insb. Mail senden per Hand, wegen pw
        password = Nutzer.erzeuge_pw()
        username, email = (self.cleaned_data['username'],
                                     self.cleaned_data['email'])

        new_user = UserenaSignup.objects.create_user(username,
                                                     email,
                                                     password,
                                                     active=False,
                                                     send_email=False)
        
        UserenaSignup.objects.filter(user=new_user).delete()
        signup = MeinUserenaSignup.objects.create(user=new_user)
        salt, hash = generate_sha1(new_user.username)
        signup.activation_key = hash
        signup.save()
        signup.send_activation_email(pw=password)
        new_user.userena_signup = signup
        new_user.save()
        
        return new_user

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


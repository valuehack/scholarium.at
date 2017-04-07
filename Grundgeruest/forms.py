from django.contrib.auth import get_user_model
from hashlib import sha1
import random
from userena.forms import SignupForm

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


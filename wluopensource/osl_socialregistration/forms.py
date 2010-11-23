from django import forms

from socialregistration.forms import UserForm

class OslUserForm(UserForm):
    email = forms.EmailField()

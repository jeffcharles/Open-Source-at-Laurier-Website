from django import forms

from socialregistration.forms import UserForm

class OslUserForm(UserForm):
    error_css_class = 'error'
    required_css_class = 'required'
    email = forms.EmailField()

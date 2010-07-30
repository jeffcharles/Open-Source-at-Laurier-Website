from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.forms import ModelForm

class OslUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=False)
    
    def save(self, commit=True):
        user = super(OslUserCreationForm, self).save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user

class UserInfoChangeForm(ModelForm):
    error_css_class = 'error'

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email')
    

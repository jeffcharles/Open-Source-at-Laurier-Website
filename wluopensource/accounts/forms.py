from django.contrib.auth.models import User
from django.forms import ModelForm

class UserInfoChangeForm(ModelForm):
    error_css_class = 'error'

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email')
    

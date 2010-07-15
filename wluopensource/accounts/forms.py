from django.contrib.auth.models import User
from django.forms import ModelForm

class UserInfoChangeForm(ModelForm):
    class Meta:
        model = User
        exclude = ('username', 'password', 'is_staff', 'is_active', 
            'is_superuser', 'last_login', 'date_joined', 'groups', 
            'user_permissions')
    

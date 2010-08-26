from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save

class UserProfile(models.Model):
    user = models.ForeignKey(User, blank=True, unique=True)
    url = models.URLField(blank=True, verify_exists=False)
    
    def __unicode__(self):
        return self.user.username
    
def profile_creation_handler(sender, **kwargs):
    if kwargs.get('created', False):
        UserProfile.objects.get_or_create(user=kwargs['instance'])
post_save.connect(profile_creation_handler, sender=User)
    

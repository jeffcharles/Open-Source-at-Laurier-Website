from django.core import urlresolvers

from osl_comments.forms import AnonOslCommentForm
from osl_comments.models import OslComment

def get_model():
    return OslComment
    
def get_form():
    return AnonOslCommentForm
    
def get_form_target():
    return urlresolvers.reverse('osl_comments.views.post_comment')
    

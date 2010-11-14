from django.core import urlresolvers

from osl_comments.forms import AnonOslCommentForm
from osl_comments.models import OslComment

ORDER_BY_NEWEST = 'newest'
ORDER_BY_OLDEST = 'oldest'
ORDER_BY_SCORE = 'score'

def get_model():
    return OslComment
    
def get_edit_form_target():
    return urlresolvers.reverse('osl_comments.views.edit_comment')
    
def get_form():
    return AnonOslCommentForm
    
def get_form_target():
    return urlresolvers.reverse('osl_comments.views.post_comment')
    

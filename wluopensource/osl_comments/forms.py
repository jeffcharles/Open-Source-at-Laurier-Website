from django import forms
from django.contrib.comments.forms import CommentForm

from osl_comments.models import OslComment

class AnonOslCommentForm(CommentForm):
    parent_comment_id = forms.IntegerField(widget=forms.HiddenInput, 
        required=False)
    
    def __init__(self, target_object, parent_comment_id=None, data=None, 
        initial=None):
        
        parent_comment_dict = {'parent_comment_id': parent_comment_id}
        if initial != None:
            initial.update(parent_comment_dict)
        else:
            initial = parent_comment_dict
            
        super(AnonOslCommentForm, self).__init__(target_object=target_object, 
            data=data, initial=initial)
        
    def get_comment_model(self):
        return OslComment
        
    def get_comment_create_data(self):
        data = super(AnonOslCommentForm, self).get_comment_create_data()
        data['parent_comment_id'] = self.cleaned_data['parent_comment_id']
        return data
        

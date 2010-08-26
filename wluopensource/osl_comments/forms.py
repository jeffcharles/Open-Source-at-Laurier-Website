from django import forms
from django.contrib.comments.forms import CommentForm, CommentSecurityForm

from osl_comments.models import OslComment

class AuthOslCommentForm(CommentSecurityForm):
    comment = CommentForm.base_fields['comment']
    honeypot = CommentForm.base_fields['honeypot']
    parent_comment_id = forms.IntegerField(widget=forms.HiddenInput, 
        required=False)
    
    def __init__(self, target_object, parent_comment_id=None, data=None, 
        initial=None):
        
        parent_comment_dict = {'parent_comment_id': parent_comment_id}
        if initial != None:
            initial.update(parent_comment_dict)
        else:
            initial = parent_comment_dict
            
        super(AuthOslCommentForm, self).__init__(target_object=target_object, 
            data=data, initial=initial)
        
    def clean_honeypot(self):
        return CommentForm.clean_honeypot(self)
        
    def get_comment_model(self):
        return OslComment
        
    def get_comment_create_data(self):
        data = CommentForm.get_comment_create_data(self)
        data.update(
            {'parent_comment_id': self.cleaned_data['parent_comment_id']}
        )
        return data
        
class AnonOslCommentForm(CommentForm, AuthOslCommentForm):

    def get_comment_create_data(self):
        data = CommentForm.get_comment_create_data(self)
        data.update(AuthOslCommentForm.get_comment_create_data(self))
        return data

    def get_comment_model(self):
        return AuthOslCommentForm.get_comment_model(self)


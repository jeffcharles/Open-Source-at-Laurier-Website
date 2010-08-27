from django import forms
from django.contrib.comments.forms import CommentForm, CommentSecurityForm

from osl_comments.models import OslComment

class AuthOslCommentForm(CommentSecurityForm):
    comment = CommentForm.base_fields['comment']
    honeypot = CommentForm.base_fields['honeypot']
    parent_comment_id = forms.IntegerField(widget=forms.HiddenInput, 
        required=False)
    
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

class OslEditCommentForm(forms.Form):
    comment = CommentForm.base_fields['comment']
    comment_id = forms.IntegerField(widget=forms.HiddenInput)
    
    def get_comment_model(self):
        return AuthOslCommentForm.get_comment_model(self)


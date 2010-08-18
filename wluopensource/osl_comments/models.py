from django.contrib.comments.models import Comment
from django.db import models

class AuthRequiredToComment(models.Model):
    application = model.CharField(max_length=255)
    auth_required = models.BooleanField()

class OslComments(Comment):
    parent_comment_pk = models.ForeignKey('self')
    inline_to_object = models.BooleanField()


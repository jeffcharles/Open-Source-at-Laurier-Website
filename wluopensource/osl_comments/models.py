from django.contrib.comments.models import Comment
from django.db import models

class OslComments(Comment):
    parent_comment_pk = models.ForeignKey('self')
    inline_to_object = models.BooleanField()
    edit_timestamp = models.DateTimeField(auto_now=False)


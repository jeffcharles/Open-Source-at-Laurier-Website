from django.contrib.comments.models import Comment
from django.db import models

class OslComment(Comment):
    parent_comment = models.ForeignKey(Comment, blank=True, null=True, related_name='parent_comment')
    inline_to_object = models.BooleanField()
    edit_timestamp = models.DateTimeField(auto_now=True)


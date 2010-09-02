from django.contrib.comments.models import Comment
from django.contrib.comments.signals import comment_was_posted, comment_will_be_posted
from django.contrib.contenttypes.models import ContentType
from django.db import models

import markdown

class OslComment(Comment):
    parent_comment = models.ForeignKey(Comment, blank=True, null=True, related_name='parent_comment')
    inline_to_object = models.BooleanField()
    edit_timestamp = models.DateTimeField()
    transformed_comment = models.TextField(editable=False)
    
    def save(self, force_insert=False, force_update=False):
        md = markdown.Markdown(safe_mode="escape")
        self.transformed_comment = md.convert(self.comment)
        
        if not self.id:
            # if new comment, not edited comment
            self.edit_timestamp = self.submit_date
        
        super(OslComment, self).save(force_insert, force_update)

def comment_success_flash_handler(sender, **kwargs):
    if 'request' in kwargs:
        kwargs['request'].flash['comment_response'] = 'Your comment has been added!'
comment_was_posted.connect(comment_success_flash_handler)

def comment_user_url_injection_handler(sender, **kwargs):
    if 'request' in kwargs and kwargs['request'].user.is_authenticated() and \
        'comment' in kwargs:
        
        comment = kwargs['comment']
        comment.url = comment.user.get_profile().url
        comment.save()
comment_was_posted.connect(comment_user_url_injection_handler)

class CommentsPerPageForContentType(models.Model):
    content_type = models.OneToOneField(ContentType)
    number_per_page = models.IntegerField()


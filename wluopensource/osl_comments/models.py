from django.contrib.comments.models import Comment
from django.contrib.comments.signals import comment_was_posted
from django.contrib.contenttypes.models import ContentType
from django.db import models

import markdown

class CommentsBannedFromIpAddress(models.Model):
    ip_address = models.IPAddressField(primary_key=True)
    comments_banned = models.BooleanField(default=True)
    
    def __unicode__(self):
        return "%s, Banned: %s" % (self.ip_address, self.comments_banned)
    
    class Meta:
        verbose_name_plural = "Comments banned from IP addresses"

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
            
        if self.user:
            self.url = self.user.get_profile().url
        
        super(OslComment, self).save(force_insert, force_update)

def comment_success_flash_handler(sender, **kwargs):
    if 'request' in kwargs:
        kwargs['request'].flash['comment_response'] = 'Your comment has been added!'
comment_was_posted.connect(comment_success_flash_handler)

class CommentsPerPageForContentType(models.Model):
    content_type = models.OneToOneField(ContentType)
    number_per_page = models.IntegerField()


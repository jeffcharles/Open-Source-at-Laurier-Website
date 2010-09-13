from django.contrib.comments.models import Comment, CommentFlag
from django.contrib.comments.signals import (comment_was_flagged, 
    comment_was_posted)
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist
from django.db import models

import markdown

from osl_comments.signals import (comment_was_deleted_by_user, 
    ip_address_ban_was_updated)

class CommentsBannedFromIpAddress(models.Model):
    ip_address = models.IPAddressField(primary_key=True)
    comments_banned = models.BooleanField(default=True)
    
    def __unicode__(self):
        return "%s, Banned: %s" % (self.ip_address, self.comments_banned)
    
    class Meta:
        permissions = (
            ("can_ban", "Can ban or un-ban IP addresses from commenting"),
        )
        verbose_name_plural = "Comments banned from IP addresses"
        
def ip_address_ban_update_success_flash_handler(sender, **kwargs):
    if 'banned' in kwargs and 'request' in kwargs:
        if kwargs['banned']:
            kwargs['request'].flash['comment_response'] = \
                'The IP address has been banned from commenting!'
        else:
            kwargs['request'].flash['comment_response'] = \
                'The IP address has been un-banned from commenting!'
ip_address_ban_was_updated.connect(ip_address_ban_update_success_flash_handler)

class OslComment(Comment):
    parent_comment = models.ForeignKey(Comment, blank=True, null=True, related_name='parent_comment')
    inline_to_object = models.BooleanField(default=False)
    edit_timestamp = models.DateTimeField()
    transformed_comment = models.TextField(editable=False)
    is_deleted_by_user = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = "comment"
    
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

def delete_success_flash_handler(sender, **kwargs):
    if 'request' in kwargs:
        kwargs['request'].flash['comment_response'] = \
            'Your comment has been deleted!'
comment_was_deleted_by_user.connect(delete_success_flash_handler)

class CommentsPerPageForContentTypeManager(models.Manager):
    
    def get_comments_per_page_for_content_type(self, content_type):
        """
        Returns the number of comments on a page for the given content type.
        """
        try:
            return self.get(content_type=content_type).number_per_page
        except ObjectDoesNotExist:
            return getattr(settings, 'DEFAULT_COMMENTS_PER_PAGE', 100)

class CommentsPerPageForContentType(models.Model):
    content_type = models.OneToOneField(ContentType)
    number_per_page = models.IntegerField()
    objects = CommentsPerPageForContentTypeManager()
    
    def __unicode__(self):
        return "%s: %s" % (self.content_type, self.number_per_page)
            
def flag_success_flash_handler(sender, **kwargs):
    if 'flag' in kwargs and \
        kwargs['flag'].flag == CommentFlag.SUGGEST_REMOVAL and \
        'created' in kwargs and kwargs['created'] and 'request' in kwargs:
        
        kwargs['request'].flash['comment_response'] = \
            'The comment has been reported!'
comment_was_flagged.connect(flag_success_flash_handler)

def moderate_success_flash_handler(sender, **kwargs):
    if 'flag' in kwargs and \
        kwargs['flag'].flag == CommentFlag.MODERATOR_DELETION and \
        'request' in kwargs:
        
        kwargs['request'].flash['comment_response'] = \
            'The comment has been moderated!'
comment_was_flagged.connect(moderate_success_flash_handler)


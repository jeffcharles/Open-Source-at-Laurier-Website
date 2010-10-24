from django.contrib.comments.models import Comment, CommentFlag
from django.contrib.comments.signals import (comment_was_flagged, 
    comment_was_posted)
from django.contrib.contenttypes.models import ContentType
from django.core import urlresolvers
from django.core.exceptions import ObjectDoesNotExist
from django.db import models

import markdown

from osl_comments.signals import (comment_was_deleted_by_user,
    comment_was_edited, ip_address_ban_was_updated)
import settings

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

class OslCommentManager(models.Manager):
    
    def get_comments(self, ctype, object_pk, order_method, paginate, 
        current_comment_page):
        """
        ctype - content type (integer)
        object_pk - object primary key (string)
        order_method - one of: latest, score, oldest
        paginate - whether or not to paginate the comments (boolean)
        current_comment_page - the current page number
        """
        
        if order_method == 'latest':
            first_order_by = 'thread_submit_date DESC'
            second_order_by = 'submit_date DESC'
        elif order_method == 'score':
            first_order_by = 'parent_score DESC'
            second_order_by = 'score DESC'
        elif order_method == 'oldest':
            first_order_by = 'thread_submit_date ASC'
            second_order_by = 'submit_date ASC'
        else:
            first_order_by = 'thread_submit_date DESC'
            second_order_by = 'submit_date DESC'
        
        num_comments_per_page = CommentsPerPageForContentType.objects.get_comments_per_page_for_content_type(
            ctype)
        
        get_threaded_comments_sql = """
            SELECT
                id,
                comment_ptr_id,
                parent,
                user_id,
                user_name,
                user_url,
                comment,
                thread_submit_date,
                submit_date,
                edit_timestamp,
                transformed_comment,
                is_removed,
                is_deleted_by_user,
                COALESCE(raw_score, 0) AS score,
                parent_comment_user_id,
                parent_comment_user_name,
                parent_comment_user_url,
                parent_comment_comment,
                parent_comment_edit_timestamp,
                parent_comment_transformed_comment,
                parent_comment_is_removed,
                parent_comment_is_deleted_by_user,
                COALESCE(raw_parent_score, 0) AS parent_score
            FROM (
                SELECT
                    dc.id,
                    oc.comment_ptr_id,
                    True AS parent,
                    dc.id AS thread_id,
                    dc.user_id,
                    dc.user_name,
                    dc.user_url,
                    dc.comment,
                    dc.submit_date AS thread_submit_date,
                    dc.submit_date,
                    dc.is_removed,
                    oc.edit_timestamp,
                    oc.transformed_comment,
                    oc.is_deleted_by_user,
                    dc.id AS parent_comment_id,
                    dc.user_id AS parent_comment_user_id,
                    dc.user_name AS parent_comment_user_name,
                    dc.user_url AS parent_comment_user_url,
                    dc.comment AS parent_comment_comment,
                    dc.is_removed AS parent_comment_is_removed,
                    oc.edit_timestamp AS parent_comment_edit_timestamp,
                    oc.transformed_comment AS parent_comment_transformed_comment,
                    oc.is_deleted_by_user AS parent_comment_is_deleted_by_user
                FROM
                    django_comments AS dc
                JOIN
                    osl_comments_oslcomment AS oc 
                    ON dc.id = oc.comment_ptr_id 
                WHERE
                    dc.content_type_id = %(content_type)d AND
                    dc.object_pk = %(object_pk)s AND
                    dc.site_id = %(site_id)d AND
                    dc.is_public = TRUE AND
                    oc.inline_to_object = False AND
                    oc.parent_comment_id IS NULL
                UNION ALL
                SELECT
                    dc2.id,
                    oc2.comment_ptr_id,
                    False AS parent,
                    oc2.parent_comment_id AS thread_id,
                    dc2.user_id,
                    dc2.user_name,
                    dc2.user_url,
                    dc2.comment,
                    dc3.submit_date AS thread_submit_date,
                    dc2.submit_date,
                    dc2.is_removed,
                    oc2.edit_timestamp,
                    oc2.transformed_comment,
                    oc2.is_deleted_by_user,
                    dc3.id AS parent_comment_id,
                    dc3.user_id AS parent_comment_user_id,
                    dc3.user_name AS parent_comment_user_name,
                    dc3.user_url AS parent_comment_user_url,
                    dc3.comment AS parent_comment_comment,
                    dc3.is_removed AS parent_comment_is_removed,
                    oc3.edit_timestamp AS parent_comment_edit_timestamp,
                    oc3.transformed_comment AS parent_comment_transformed_comment,
                    oc3.is_deleted_by_user AS parent_comment_is_deleted_by_user
                FROM
                    django_comments AS dc2
                JOIN
                    osl_comments_oslcomment AS oc2
                    ON dc2.id = oc2.comment_ptr_id
                JOIN
                    django_comments AS dc3
                    ON dc3.id = oc2.parent_comment_id
                JOIN
                    osl_comments_oslcomment AS oc3
                    ON dc3.id = oc3.comment_ptr_id
                WHERE
                    dc2.content_type_id = %(content_type)d AND
                    dc2.object_pk = %(object_pk)s AND
                    dc2.site_id = %(site_id)d AND
                    dc2.is_public = True AND
                    oc2.inline_to_object = False AND
                    oc2.parent_comment_id IS NOT NULL
                ) AS t
            LEFT JOIN (
                SELECT
                    object_id,
                    SUM(vote) AS raw_score
                FROM
                    votes
                JOIN 
                    django_content_type
                    ON votes.content_type_id = django_content_type.id
                WHERE
                    app_label = 'osl_comments' AND
                    model = 'oslcomment' AND
                    object_id IN (
                        SELECT
                            id
                        FROM
                            django_comments
                        WHERE
                            content_type_id = %(content_type)d AND
                            object_pk = %(object_pk)s
                    )
                GROUP BY
                    object_id
            ) AS t2
                ON t.id = t2.object_id
            LEFT JOIN (
                SELECT
                    object_id,
                    SUM(vote) AS raw_parent_score
                FROM
                    votes
                JOIN 
                    django_content_type
                    ON votes.content_type_id = django_content_type.id
                WHERE
                    app_label = 'osl_comments' AND
                    model = 'oslcomment' AND
                    object_id IN (
                        SELECT
                            id
                        FROM
                            django_comments
                        WHERE
                            content_type_id = %(content_type)d AND
                            object_pk = %(object_pk)s
                    )
                GROUP BY
                    object_id
            ) AS t3
                ON t.parent_comment_id = t3.object_id
            ORDER BY
                %(first_thread_order_by)s,
                thread_id ASC,
                parent DESC,
                %(second_thread_order_by)s
        """ % {
            'content_type': ctype.id,
            'object_pk': "'%s'" % object_pk,
            'site_id': settings.SITE_ID,
            'first_thread_order_by': first_order_by,
            'second_thread_order_by': second_order_by,
        }
        
        limit_sql = """
            LIMIT
                %(limit)d
            OFFSET
                %(offset)d
        """ % {
            'limit': num_comments_per_page, 
            'offset': (current_comment_page - 1) * num_comments_per_page
        }
        
        if paginate:
            sql = ''.join([get_threaded_comments_sql, limit_sql])
        else:
            sql = get_threaded_comments_sql
        
        qs = self.raw(sql)

        return qs

class OslComment(Comment):
    parent_comment = models.ForeignKey(Comment, blank=True, null=True, related_name='parent_comment')
    inline_to_object = models.BooleanField(db_index=True, default=False)
    edit_timestamp = models.DateTimeField()
    transformed_comment = models.TextField(editable=False)
    is_deleted_by_user = models.BooleanField(default=False)
    objects = OslCommentManager()
    
    class Meta:
        verbose_name = "comment"
        
    def get_content_object_url(self):
        """
        Get a URL suitable for redirecting to the content object.
        """
        return urlresolvers.reverse(
            "osl-comments-url-redirect",
            args=(self.content_type_id, self.object_pk)
        )
        
    def is_flagged(self):
        """Returns true if comment is flagged for moderation."""
        return (
            CommentFlag.objects.filter(comment=self)
            .filter(flag=CommentFlag.SUGGEST_REMOVAL).exists()
        )
        
    
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

def edit_success_flash_hanlder(sender, **kwargs):
    if 'request' in kwargs:
        kwargs['request'].flash['comment_response'] = \
            'Your comment has been edited!'
comment_was_edited.connect(edit_success_flash_hanlder)

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


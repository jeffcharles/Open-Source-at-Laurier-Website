from django.contrib.comments.models import Comment, CommentFlag
from django.contrib.comments.signals import (comment_was_flagged, 
    comment_was_posted)
from django.contrib.contenttypes.models import ContentType
from django.core import urlresolvers
from django.core.exceptions import ObjectDoesNotExist
from django.db import models

import markdown

import osl_comments
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

    _num_comments_per_page = None
    
    def _get_num_comments_per_page(self, ctype):
        if self._num_comments_per_page == None:
            self._num_comments_per_page = CommentsPerPageForContentType.objects.get_comments_per_page_for_content_type(
            ctype)
        return self._num_comments_per_page

    def get_comments(self, ctype, object_pk, order_method, paginate=True, 
        comment_page=None, offset=None):
        
        if comment_page == None and offset == None:
            raise Exception("Either comment_page or offset argument needs to be provided")
        if offset == None:
            offset = (comment_page - 1) * self._get_num_comments_per_page(ctype)
        return self._get_comments(ctype, object_pk, order_method, paginate, 
            offset)

    def _get_comments(self, ctype, object_pk, order_method, paginate, offset):
        """
        ctype - content type (integer)
        object_pk - object primary key (string)
        order_method - one of the order by constants set in __init__.py
        paginate - whether or not to paginate the comments (boolean)
        offset - the offset
        """
        
        num_comments_per_page = self._get_num_comments_per_page(ctype)
        
        get_threaded_comments_sql = """
            SELECT
                id,
                comment_ptr_id,
                parent,
                content_type_id,
                object_pk,
                thread_id,
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
        """
        if order_method == 'score':
            get_threaded_comments_sql += """
                COALESCE(raw_score, 0) AS score,
                COALESCE(raw_parent_score, 0) AS parent_score
            """
        else:
            get_threaded_comments_sql += """
                raw_score AS score
            """
        get_threaded_comments_sql += """
            FROM (
                SELECT
                    dc.id,
                    oc.comment_ptr_id,
                    True AS parent,
                    dc.content_type_id,
                    dc.object_pk,
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
                    oc.parent_comment_id,
        """
        if order_method == 'score':
            get_threaded_comments_sql += """
                        score.raw_score,
                        score.raw_score AS raw_parent_score
        """
        else:
            get_threaded_comments_sql += """
                        score.raw_score
        """
        get_threaded_comments_sql += """
                FROM
                    django_comments AS dc
                JOIN
                    osl_comments_oslcomment AS oc 
                    ON dc.id = oc.comment_ptr_id 
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
                        model = 'oslcomment'
                    GROUP BY
                        object_id
                ) AS score
                    ON dc.id = score.object_id
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
                    dc2.content_type_id,
                    dc2.object_pk,
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
                    oc2.parent_comment_id,
        """ % {
            'content_type': ctype.id,
            'object_pk': "'%s'" % object_pk,
            'site_id': settings.SITE_ID
        }
        if order_method == 'score':
            get_threaded_comments_sql += """
                    score2.raw_score,
                    score3.raw_parent_score
        """
        else:
            get_threaded_comments_sql += """
                    score2.raw_score
        """
        get_threaded_comments_sql += """
                FROM
                    django_comments AS dc2
                JOIN
                    osl_comments_oslcomment AS oc2
                    ON dc2.id = oc2.comment_ptr_id
                JOIN
                    django_comments AS dc3
                    ON dc3.id = oc2.parent_comment_id
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
                        model = 'oslcomment'
                    GROUP BY
                        object_id
                ) AS score2
                    ON dc2.id = score2.object_id
        """ % {
            'content_type': ctype.id,
            'object_pk': "'%s'" % object_pk,
            'site_id': settings.SITE_ID
        }
        if order_method == 'score':
            get_threaded_comments_sql += """
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
                        model = 'oslcomment'
                    GROUP BY
                        object_id
                ) AS score3
                    ON oc2.parent_comment_id = score3.object_id
        """
        get_threaded_comments_sql += """
                WHERE
                    dc2.content_type_id = %(content_type)d AND
                    dc2.object_pk = %(object_pk)s AND
                    dc2.site_id = %(site_id)d AND
                    dc2.is_public = True AND
                    oc2.inline_to_object = False AND
                    oc2.parent_comment_id IS NOT NULL
                ) AS t
        """ % {
            'content_type': ctype.id,
            'object_pk': "'%s'" % object_pk,
            'site_id': settings.SITE_ID
        }
        
        if order_method == osl_comments.ORDER_BY_SCORE:
            get_threaded_comments_sql += """
                ORDER BY
                    parent_score DESC,
                    thread_submit_date DESC,
                    thread_id ASC,
                    parent DESC,
                    score DESC,
                    submit_date DESC
            """
        else:
            if order_method == osl_comments.ORDER_BY_NEWEST:
                first_order_by = 'thread_submit_date DESC'
                second_order_by = 'submit_date DESC'
            elif order_method == osl_comments.ORDER_BY_OLDEST:
                first_order_by = 'thread_submit_date ASC'
                second_order_by = 'submit_date ASC'
            else:
                first_order_by = 'thread_submit_date DESC'
                second_order_by = 'submit_date DESC'
            
            get_threaded_comments_sql += """
                ORDER BY
                    %(first_thread_order_by)s,
                    thread_id ASC,
                    parent DESC,
                    %(second_thread_order_by)s
            """ % {
                'first_thread_order_by': first_order_by,
                'second_thread_order_by': second_order_by
            }
        
        limit_sql = """
            LIMIT
                %(limit)d
            OFFSET
                %(offset)d
        """ % {
            'limit': num_comments_per_page, 
            'offset': offset
        }
        
        if paginate:
            sql = ''.join([get_threaded_comments_sql, limit_sql])
        else:
            sql = get_threaded_comments_sql
        
        qs = self.raw(sql)
        
        return qs

class OslComment(Comment):
    """
    >>> import datetime
    >>> c1 = OslComment(content_type_id=1, object_pk=1, site_id=1, \
            user_id=None, user_name='test', user_email='test@test.ca', \
            user_url='', comment='1', ip_address='127.0.0.1', \
            parent_comment_id=None, submit_date=datetime.datetime.now())
    >>> c1.save()
    >>> c1a = OslComment(content_type_id=1, object_pk=1, site_id=1, \
            user_id=None, user_name='test', user_email='test@test.ca', \
            user_url='', comment='1a', ip_address='127.0.0.1', \
            parent_comment_id=c1.id, submit_date=datetime.datetime.now())
    >>> c1a.save()
    >>> c2 = OslComment(content_type_id=1, object_pk=1, site_id=1, \
            user_id=None, user_name='test', user_email='test@test.ca', \
            user_url='', comment='2', ip_address='127.0.0.1', \
            parent_comment_id=None, submit_date=datetime.datetime.now())
    >>> c2.save()
    >>> c1b = OslComment(content_type_id=1, object_pk=1, site_id=1, \
            user_id=None, user_name='test', user_email='test@test.ca', \
            user_url='', comment='1b', ip_address='127.0.0.1', \
            parent_comment_id=c1.id, submit_date=datetime.datetime.now())
    >>> c1b.save()
    >>> c2a = OslComment(content_type_id=1, object_pk=1, site_id=1, \
            user_id=None, user_name='test', user_email='test@test.ca', \
            user_url='', comment='2a', ip_address='127.0.0.1', \
            parent_comment_id=c2.id, submit_date=datetime.datetime.now())
    >>> c2a.save()
    >>> c3 = OslComment(content_type_id=1, object_pk=1, site_id=1, \
            user_id=None, user_name='test', user_email='test@test.ca', \
            user_url='', comment='3', ip_address='127.0.0.1', \
            parent_comment_id=None, submit_date=datetime.datetime.now())
    >>> c3.save()
    >>> c1c = OslComment(content_type_id=1, object_pk=1, site_id=1, \
            user_id=None, user_name='test', user_email='test@test.ca', \
            user_url='', comment='1c', ip_address='127.0.0.1', \
            parent_comment_id=c1.id, submit_date=datetime.datetime.now())
    >>> c1c.save()
    >>> c3a = OslComment(content_type_id=1, object_pk=1, site_id=1, \
            user_id=None, user_name='test', user_email='test@test.ca', \
            user_url='', comment='3a', ip_address='127.0.0.1', \
            parent_comment_id=c3.id, submit_date=datetime.datetime.now())
    >>> c3a.save()
    >>> c2b = OslComment(content_type_id=1, object_pk=1, site_id=1, \
            user_id=None, user_name='test', user_email='test@test.ca', \
            user_url='', comment='2b', ip_address='127.0.0.1', \
            parent_comment_id=c2.id, submit_date=datetime.datetime.now())
    >>> c2b.save()
    >>> c3b = OslComment(content_type_id=1, object_pk=1, site_id=1, \
            user_id=None, user_name='test', user_email='test@test.ca', \
            user_url='', comment='3b', ip_address='127.0.0.1', \
            parent_comment_id=c3.id, submit_date=datetime.datetime.now())
    >>> c3b.save()
    >>> c3c = OslComment(content_type_id=1, object_pk=1, site_id=1, \
            user_id=None, user_name='test', user_email='test@test.ca', \
            user_url='', comment='3c', ip_address='127.0.0.1', \
            parent_comment_id=c3.id, submit_date=datetime.datetime.now())
    >>> c3c.save()
    >>> c2c = OslComment(content_type_id=1, object_pk=1, site_id=1, \
            user_id=None, user_name='test', user_email='test@test.ca', \
            user_url='', comment='2c', ip_address='127.0.0.1', \
            parent_comment_id=c2.id, submit_date=datetime.datetime.now())
    >>> c2c.save()
    
    >>> from voting.models import Vote
    >>> from django.contrib.auth.models import User
    >>> user = User.objects.create_user('tester', 'tester@test.ca', 'password')
    >>> Vote.objects.record_vote(c1b, user, 1)
    >>> Vote.objects.record_vote(c2, user, 1)
    >>> Vote.objects.record_vote(c2a, user, 1)
    >>> Vote.objects.record_vote(c3c, user, 1)
    
    >>> from django.contrib.contenttypes.models import ContentType
    >>> ctype = ContentType.objects.get(id=1)
    
    >>> comments_by_newest = list(OslComment.objects.get_comments(ctype, '1', \
            'newest', comment_page=1))
    >>> [comment.comment for comment in comments_by_newest]
    [u'3', u'3c', u'3b', u'3a', u'2', u'2c', u'2b', u'2a', u'1', u'1c', u'1b', \
        u'1a']
        
    >>> comments_by_oldest = list(OslComment.objects.get_comments(ctype, '1', \
            'oldest', comment_page=1))
    >>> [comment.comment for comment in comments_by_oldest]
    [u'1', u'1a', u'1b', u'1c', u'2', u'2a', u'2b', u'2c', u'3', u'3a', u'3b', \
        u'3c']
    
    >>> comments_by_score = list(OslComment.objects.get_comments(ctype, '1', \
            'score', comment_page=1))
    >>> [comment.comment for comment in comments_by_score]
    [u'2', u'2a', u'2c', u'2b', u'3', u'3c', u'3b', u'3a', u'1', u'1b', u'1c', \
        u'1a']
    """

    parent_comment = models.ForeignKey(Comment, blank=True, db_index=True, null=True, related_name='parent_comment')
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
            return getattr(settings, 'DEFAULT_COMMENTS_PER_PAGE', 50)

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


from django import template
from django.conf import settings
from django.contrib import comments
from django.contrib.comments.templatetags.comments import CommentListNode
from django.utils.encoding import smart_unicode

register = template.Library()

class OslCommentListNode(CommentListNode):
    """Insert a list of comments into the context."""
    
    def __init__(self, ctype=None, object_pk_expr=None, object_expr=None, as_varname=None, comment=None, sorted_by=None, limit=None, offset=None):
        if ctype is None and object_expr is None:
            raise template.TemplateSyntaxError("Comment nodes must be given either a literal object or a ctype and object pk.")
        self.comment_model = comments.get_model()
        self.as_varname = as_varname
        self.ctype = ctype
        self.object_pk_expr = object_pk_expr
        self.object_expr = object_expr
        self.comment = comment
        self.sorted_by = sorted_by
        self.limit = limit
        self.offset = offset
    
    def get_query_set(self, context):
        ctype, object_pk = self.get_target_ctype_pk(context)
        if not object_pk:
            return self.comment_model.objects.none()
        
        if self.sorted_by == 'oldest':
            first_order_by = 'thread_submit_date ASC'
            second_order_by = 'submit_date ASC'
        elif self.sorted_by == 'newest':
            first_order_by = 'thread_submit_date DESC'
            second_order_by = 'submit_date DESC'
        else:
            first_order_by = 'thread_submit_date DESC'
            second_order_by = 'submit_date DESC'
        
        removed_comments_condition = 'id IS NOT NULL'    
        if getattr(settings, 'COMMENTS_HIDE_REMOVED', True):
            removed_comments_condition = 'is_removed = False'
        
        get_threaded_comments_sql = """
            SELECT
                id,
                parent,
                user_name,
                user_url,
                comment,
                thread_submit_date,
                submit_date,
                edit_timestamp
            FROM (
                SELECT
                    dc.id,
                    True AS parent,
                    dc.id AS thread_id,
                    dc.user_name,
                    dc.user_url,
                    dc.comment,
                    dc.submit_date AS thread_submit_date,
                    dc.submit_date,
                    oc.edit_timestamp
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
                    dc.%(removed_comments_condition)s AND
                    oc.inline_to_object = False AND
                    oc.parent_comment_id IS NULL
                UNION
                SELECT
                    dc2.id,
                    False AS parent,
                    oc2.parent_comment_id AS thread_id,
                    dc2.user_name,
                    dc2.user_url,
                    dc2.comment,
                    dc3.submit_date AS thread_submit_date,
                    dc2.submit_date,
                    oc2.edit_timestamp
                FROM
                    django_comments AS dc2
                JOIN
                    osl_comments_oslcomment AS oc2
                    ON dc2.id = oc2.comment_ptr_id
                JOIN
                    django_comments AS dc3
                    ON dc3.id = oc2.parent_comment_id
                WHERE
                    dc2.content_type_id = %(content_type)d AND
                    dc2.object_pk = %(object_pk)s AND
                    dc2.site_id = %(site_id)d AND
                    dc2.is_public = True AND
                    dc2.%(removed_comments_condition)s AND
                    dc3.%(removed_comments_condition)s AND
                    oc2.inline_to_object = False AND
                    oc2.parent_comment_id IS NOT NULL
                ) AS t
            ORDER BY
                %(first_thread_order_by)s,
                thread_id ASC,
                parent DESC,
                %(second_thread_order_by)s
            LIMIT
                %(limit)d
            OFFSET
                %(offset)d
        """ % {
            'content_type': ctype.id,
            'object_pk': "'%s'" % object_pk,
            'site_id': settings.SITE_ID,
            'removed_comments_condition': removed_comments_condition,
            'first_thread_order_by': first_order_by,
            'second_thread_order_by': second_order_by,
            'limit': self.limit, 
            'offset': self.offset
        }
        
        qs = self.comment_model.objects.raw(get_threaded_comments_sql)

        return qs
    
    @classmethod
    def handle_token(cls, parser, token):
        tokens = token.contents.split()
        if tokens[1] != 'for':
            raise template.TemplateSyntaxError("Second argument in %r tag must be 'for'" % tokens[0])

        # {% get_comment_list for obj as varname limit int offset int %}
        if len(tokens) == 9:
            if tokens[3] != 'as':
                raise template.TemplateSyntaxError("Third argument in %r must be 'as'" % tokens[0])
            if tokens[5] != 'limit':
                raise template.TemplateSyntaxError("Fifth argument in %r must be 'limit'" % tokens[0])
            if tokens[7] != 'offset':
                raise template.TemplateSyntaxError("Seventh argument in %r must be 'offset'" % tokens[0])
            return cls(
                object_expr = parser.compile_filter(tokens[2]),
                as_varname = tokens[4],
                limit = int(tokens[6]),
                offset = int(tokens[8])
            )

        # {% get_comment_list for app.model pk as varname limit int offset int %}
        elif len(tokens) == 10:
            if tokens[4] != 'as':
                raise template.TemplateSyntaxError("Fourth argument in %r must be 'as'" % tokens[0])
            if tokens[6] != 'limit':
                raise template.TemplateSyntaxError("Sixth argument in %r must be 'limit'" % tokens[0])
            if tokens[8] != 'offset':
                raise template.TemplateSyntaxError("Eighth argument in %r must be 'offset'" % tokens[0])
            return cls(
                ctype = BaseCommentNode.lookup_content_type(tokens[2], tokens[0]),
                object_pk_expr = parser.compile_filter(tokens[3]),
                as_varname = tokens[5],
                limit = int(tokens[7]),
                offset = int(tokens[9])
            )
            
        # {% get_comment_list for obj as varname sorted by column limit int offset int %}
        elif len(tokens) == 12:
            if tokens[3] != 'as':
                raise template.TemplateSyntaxError("Third argument in %r must be 'as'" % tokens[0])
            if tokens[5] != 'sorted':
                raise template.TemplateSyntaxError("Fifth argument in %r must be 'sorted'" % tokens[0])
            if tokens[6] != 'by':
                raise template.TemplateSyntaxError("Sixth argument in %r must be 'by'" % tokens[0])
            if tokens[8] != 'limit':
                raise template.TemplateSyntaxError("Eighth argument in %r must be 'limit'" % tokens[0])
            if tokens[10] != 'offset':
                raise template.TemplateSyntaxError("Tenth argument in %r must be 'offset'" % tokens[0])
            return cls(
                object_expr = parser.compile_filter(tokens[2]),
                as_varname = tokens[4],
                sorted_by = tokens[7],
                limit = int(tokens[9]),
                offset = int(tokens[11])
            )
            
        # {% get_comment_list for app.model pk as varname sorted by column limit int offset int %}
        elif len(tokens) == 13:
            if tokens[4] != 'as':
                raise template.TemplateSyntaxError("Fourth argument in %r must be 'as'" % tokens[0])
            if tokens[6] != 'sorted':
                raise template.TemplateSyntaxError("Sixth argument in %r must be 'sorted'" % tokens[0])
            if tokens[7] != 'by':
                raise template.TemplateSyntaxError("Seventh argument in %r must be 'by'" % tokens[0])
            if tokens[9] != 'limit':
                raise template.TemplateSyntaxError("Ninth argument in %r must be 'limit'" % tokens[0])
            if tokens[11] != 'offset':
                raise template.TemplateSyntaxError("Eleventh argument in %r must be 'offset'" % tokens[0])
            return cls(
                ctype = BaseCommentNode.lookup_content_type(tokens[2], tokens[0]),
                object_pk_expr = parser.compile_filter(tokens[3]),
                as_varname = tokens[5],
                sorted_by = tokens[8],
                limit = int(tokens[10]),
                offset = int(tokens[11])
            )

        else:
            raise template.TemplateSyntaxError("%r tag requires 8, 9, 11, or 12 arguments" % tokens[0])
        
@register.tag
def get_threaded_comment_list(parser, token):
    """
    Gets the list of comments for the given params and populates the template
    context with a variable containing that value, whose name is defined by the
    'as' clause. Limit is the maximum number of comments to return and offset
    is the size of the offset (used for pagination).

    Syntax::

        {% get_threaded_comment_list for [object] as [varname]  %}
        {% get_threaded_comment_list for [app].[model] [object_id] as [varname]  %}
        {% get_threaded_comment_list for [object] as [varname] sorted by [column] %}
        {% get_threaded_comment_list for [app].[model] [object_id] as [varname] sorted by [column] %}

    Example usage::

        {% get_threaded_comment_list for event as comment_list %}
        {% for comment in comment_list %}
            ...
        {% endfor %}

    """
    return OslCommentListNode.handle_token(parser, token)


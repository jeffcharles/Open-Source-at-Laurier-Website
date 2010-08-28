from django import template
from django.conf import settings
from django.contrib import comments
from django.contrib.comments.templatetags.comments import BaseCommentNode, CommentFormNode, CommentListNode, RenderCommentFormNode
from django.core.paginator import Paginator
from django.template.loader import render_to_string
from django.utils.encoding import smart_unicode

import osl_comments
from osl_comments.forms import AnonOslCommentForm, AuthOslCommentForm, OslEditCommentForm
from osl_comments.models import CommentsPerPageForContentType, OslComment

register = template.Library()

class AbstractUrlNode(template.Node):
    query_string_key = None
    type_of_object = None
    
    def __init__(self, comment_object):
        if comment_object is None:
            raise template.TemplateSyntaxError(
                "%s objects must be given a valid comment." % self.type_of_object
            )
        self.comment_object = comment_object
    
    def render(self, context):
        comment = self.comment_object.resolve(context)
        query_string = context['request'].GET.copy()
        query_string.update({('%s' % self.query_string_key): comment.id})
        return ''.join(['?', query_string.urlencode()])

class AnonOslCommentFormNode(CommentFormNode):
    
    def __init__(self, ctype=None, object_pk_expr=None, object_expr=None, 
        as_varname=None, comment=None, parent_comment_id=None):
        
        super(AnonOslCommentFormNode, self).__init__(ctype=ctype, 
            object_pk_expr=object_pk_expr, object_expr=object_expr, 
            as_varname=as_varname, comment=comment)
        self.parent_comment_id = parent_comment_id
    
    def get_form(self, context):
        ctype, object_pk = self.get_target_ctype_pk(context)
        if self.parent_comment_id is not None:
            parent_comment_id = self.parent_comment_id.resolve(context)
        else:
            parent_comment_id = None
        if object_pk:
            target_object = ctype.get_object_for_this_type(pk=object_pk)
            initial = {'parent_comment_id': parent_comment_id}
            if context['request'].user.is_authenticated():
                return AuthOslCommentForm(
                    target_object = target_object, initial = initial
                )
            else:
                return AnonOslCommentForm(
                    target_object = target_object, initial = initial
                )
        else:
            return None
            
    @classmethod
    def handle_token(cls, parser, token):
        tokens = token.contents.split()
        if tokens[1] != 'for':
            raise template.TemplateSyntaxError("First argument in %r tag must be 'for'" % tokens[0])
            
        # {% get_anon_comment_form for obj as varname %}
        if len(tokens) == 5:
            if tokens[3] != 'as':
                raise template.TemplateSyntaxError("Third argument in %r tag must be 'as'" % tokens[0])
            return cls(
                object_expr = parser.compile_filter(tokens[2]),
                as_varname = tokens[4]
            )
            
        # {% get_anon_comment_form for app.model pk as varname %}
        if len(tokens) == 6:
            if tokens[4] != 'as':
                raise template.TemplateSyntaxError("Fourth argument in %r tag must be 'as'" % tokens[0])
            return cls(
                ctype = BaseCommentNode.lookup_content_type(tokens[2], tokens[0]),
                object_pk_expr = parser.compile_filter(tokens[3]),
                as_varname = tokens[5]
            )
        
        # {% get_anon_comment_form for obj replying to parent_comment_id as varname %}
        if len(tokens) == 8:
            if tokens[3] != 'replying':
                raise template.TemplateSyntaxError("Third argument in %r tag must be 'replying'" % tokens[0])
            if tokens[4] != 'to':
                raise template.TemplateSyntaxError("Fourth argument in %r tag must be 'to'" % tokens[0])
            if tokens[6] != 'as':
                raise template.TemplateSyntaxError("Sixth argument in %r tag must be 'as'" % tokens[0])
            return cls(
                object_expr = parser.compile_filter(tokens[2]),
                parent_comment_id = parser.compile_filter(tokens[5]),
                as_varname = tokens[7]
            )
            
        # {% get_anon_comment_form for app.model pk replying to parent_comment_id as varname %}
        if len(tokens) == 9:
            if tokens[4] != 'replying':
                raise template.TemplateSyntaxError("Fourth argument in %r tag must be 'replying'" % tokens[0])
            if tokens[5] != 'to':
                raise template.TemplateSyntaxError("Fifth argument in %r tag must be 'to'" % tokens[0])
            if tokens[7] != 'as':
                raise template.TemplateSyntaxError("Seventh argument in %r tag must be 'as'" % tokens[0])
            return cls(
                ctype = BaseCommentNode.lookup_content_type(tokens[2], tokens[0]),
                object_pk_expr = parser.compile_filter(tokens[3]),
                parent_comment_id = parser.compile_filter(tokens[6]),
                as_varname = tokens[8]
            )
        
        else:
            raise template.TemplateSyntaxError("%r tag requires 4, 5, 7, or 8 arguments" % tokens[0])

class CommentPaginationPageNode(BaseCommentNode):
    """Insert a comment pagination object into the context."""
    
    def __init__(self, ctype=None, object_pk_expr=None, object_expr=None, 
        as_varname=None):
        
        if ctype is None and object_expr is None:
            raise template.TemplateSyntaxError(
                "Comment nodes must be given either a literal object or a \
                ctype and object pk."
            )
        self.ctype = ctype
        self.object_pk_expr = object_pk_expr
        self.object_expr = object_expr
        self.as_varname = as_varname
        
    def render(self, context):
        ctype, object_pk = self.get_target_ctype_pk(context)
        if object_pk is None:
            comment_list = []
        
        comment_list = OslComment.objects.filter(
            content_type = ctype,
            object_pk = smart_unicode(object_pk),
            site__pk = settings.SITE_ID,
            is_public = True
        )

        if getattr(settings, 'COMMENTS_HIDE_REMOVED', True):
            comment_list = comment_list.filter(is_removed=False)
        
        comment_paginator = Paginator(comment_list, 
            get_comments_per_page_for_content_type(ctype))
        context[self.as_varname] = comment_paginator.page(
            get_comment_page(context))
        return ''

class EditUrlNode(AbstractUrlNode):
    query_string_key = 'edit_comment'
    type_of_object = 'Edit'

class OslCommentListNode(CommentListNode):
    """Insert a list of comments into the context."""
    
    def __init__(self, ctype=None, object_pk_expr=None, object_expr=None, 
        as_varname=None, comment=None, sorted_by=None):
    
        super(OslCommentListNode, self).__init__(ctype=ctype, 
            object_pk_expr=object_pk_expr, object_expr=object_expr, 
            as_varname=as_varname, comment=comment)
            
        self.sorted_by = sorted_by
    
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
            
        num_comments_per_page = get_comments_per_page_for_content_type(ctype)
        
        get_threaded_comments_sql = """
            SELECT
                id,
                comment_ptr_id,
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
                    oc.comment_ptr_id,
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
                    oc2.comment_ptr_id,
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
            'limit': num_comments_per_page, 
            'offset': (get_comment_page(context) - 1) * num_comments_per_page
        }
        
        qs = self.comment_model.objects.raw(get_threaded_comments_sql)

        return qs
    
    @classmethod
    def handle_token(cls, parser, token):
        tokens = token.contents.split()
        if tokens[1] != 'for':
            raise template.TemplateSyntaxError("Second argument in %r tag must be 'for'" % tokens[0])

        # {% get_comment_list for obj as varname %}
        if len(tokens) == 5:
            if tokens[3] != 'as':
                raise template.TemplateSyntaxError("Third argument in %r must be 'as'" % tokens[0])
            return cls(
                object_expr = parser.compile_filter(tokens[2]),
                as_varname = tokens[4],
            )

        # {% get_comment_list for app.model pk as varname %}
        elif len(tokens) == 6:
            if tokens[4] != 'as':
                raise template.TemplateSyntaxError("Fourth argument in %r must be 'as'" % tokens[0])
            return cls(
                ctype = BaseCommentNode.lookup_content_type(tokens[2], tokens[0]),
                object_pk_expr = parser.compile_filter(tokens[3]),
                as_varname = tokens[5],
            )
            
        # {% get_comment_list for obj as varname sorted by column %}
        elif len(tokens) == 8:
            if tokens[3] != 'as':
                raise template.TemplateSyntaxError("Third argument in %r must be 'as'" % tokens[0])
            if tokens[5] != 'sorted':
                raise template.TemplateSyntaxError("Fifth argument in %r must be 'sorted'" % tokens[0])
            if tokens[6] != 'by':
                raise template.TemplateSyntaxError("Sixth argument in %r must be 'by'" % tokens[0])
            return cls(
                object_expr = parser.compile_filter(tokens[2]),
                as_varname = tokens[4],
                sorted_by = tokens[7],
            )
            
        # {% get_comment_list for app.model pk as varname sorted by column %}
        elif len(tokens) == 9:
            if tokens[4] != 'as':
                raise template.TemplateSyntaxError("Fourth argument in %r must be 'as'" % tokens[0])
            if tokens[6] != 'sorted':
                raise template.TemplateSyntaxError("Sixth argument in %r must be 'sorted'" % tokens[0])
            if tokens[7] != 'by':
                raise template.TemplateSyntaxError("Seventh argument in %r must be 'by'" % tokens[0])
            return cls(
                ctype = BaseCommentNode.lookup_content_type(tokens[2], tokens[0]),
                object_pk_expr = parser.compile_filter(tokens[3]),
                as_varname = tokens[5],
                sorted_by = tokens[8],
            )

        else:
            raise template.TemplateSyntaxError("%r tag requires 4, 5, 7, or 8 arguments" % tokens[0])
            
class OslEditCommentFormNode(CommentFormNode):
    
    def __init__(self, as_varname=None, comment=None):
        
        if comment is None:
            raise template.TemplateSyntaxError(
                "Edit comment form node must be given a comment object."
            )
        self.comment_model = comments.get_model()
        self.as_varname = as_varname
        self.comment = comment
        
    def get_form(self, context):
        comment = self.comment.resolve(context)
        if context['request'].user.is_authenticated():
            return OslEditCommentForm(
                initial = {
                    'comment_id': comment.id,
                    'comment': comment.comment
                }
            )
        else:
            return None
            
    @classmethod
    def handle_token(cls, parser, token):
        tokens = token.contents.split()
        if tokens[1] != 'for':
            raise template.TemplateSyntaxError("First argument in %r tag must be 'for'" % tokens[0])
            
        # {% get_edit_comment_form for comment as varname %}
        if len(tokens) == 5:
            if tokens[3] != 'as':
                raise template.TemplateSyntaxError("Third argument in %r tag must be 'as'" % tokens[0])
            return cls(
                comment = parser.compile_filter(tokens[2]),
                as_varname = tokens[4]
            )
        else:
            raise template.TemplateSyntaxError("%r tag takes 4 arguments" % tokens[0])
                

class RenderAnonOslCommentFormNode(AnonOslCommentFormNode, 
    RenderCommentFormNode):

    @classmethod
    def handle_token(cls, parser, token):
        tokens = token.contents.split()
        if tokens[1] != 'for':
            raise template.TemplateSyntaxError("First argument in %r tag must be 'for'" % tokens[0])
            
        # {% render_anon_comment_form for obj %}
        if len(tokens) == 3:
            return cls(
                object_expr = parser.compile_filter(tokens[2])
            )
            
        # {% render_anon_comment_form for app.model pk %}
        if len(tokens) == 4:
            return cls(
                ctype = BaseCommentNode.lookup_content_type(tokens[2], tokens[0]),
                object_pk_expr = parser.compile_filter(tokens[3])
            )
        
        # {% render_anon_comment_form for obj replying to parent_comment_id %}
        if len(tokens) == 6:
            if tokens[3] != 'replying':
                raise template.TemplateSyntaxError("Third argument in %r tag must be 'replying'" % tokens[0])
            if tokens[4] != 'to':
                raise template.TemplateSyntaxError("Fourth argument in %r tag must be 'to'" % tokens[0])
            return cls(
                object_expr = parser.compile_filter(tokens[2]),
                parent_comment_id = parser.compile_filter(tokens[5])
            )
            
        # {% render_anon_comment_form for app.model pk replying to parent_comment_id %}
        if len(tokens) == 7:
            if tokens[4] != 'replying':
                raise template.TemplateSyntaxError("Fourth argument in %r tag must be 'replying'" % tokens[0])
            if tokens[5] != 'to':
                raise template.TemplateSyntaxError("Fifth argument in %r tag must be 'to'" % tokens[0])
            return cls(
                ctype = BaseCommentNode.lookup_content_type(tokens[2], tokens[0]),
                object_pk_expr = parser.compile_filter(tokens[3]),
                parent_comment_id = parser.compile_filter(tokens[6])
            )
        
        else:
            raise template.TemplateSyntaxError("%r tag requires 2, 3, 5, or 6 arguments" % tokens[0])
        
class RenderOslEditCommentNode(OslEditCommentFormNode):
    
    @classmethod
    def handle_token(cls, parser, token):
        tokens = token.contents.split()
        if tokens[1] != 'for':
            raise template.TemplateSyntaxError("First argument in %r tag must be 'for'" % tokens[0])
            
        # {% render_anon_comment_form for obj %}
        if len(tokens) == 3:
            return cls(
                comment = parser.compile_filter(tokens[2])
            )
            
    def render(self, context):
        comment = self.comment.resolve(context)
        ctype = comment.content_type
        if context['request'].user.is_authenticated():
            template_search_list = [
                "comments/%s/%s/edit_form.html" % (ctype.app_label, ctype.model),
                "comments/%s/edit_form.html" % ctype.app_label,
                "comments/edit_form.html"
            ]
            context.push()
            formstr = render_to_string(template_search_list, {"form" : self.get_form(context)}, context)
            context.pop()
            return formstr
        else:
            return ''
        
class ReplyUrlNode(AbstractUrlNode):
    query_string_key = 'reply_to'
    type_of_object = 'Reply'

def get_comments_per_page_for_content_type(content_type):
    """Returns the number of comments on a page for the given content type."""
    try:
        return CommentsPerPageForContentType.objects.get(content_type=content_type).number_per_page
    except CommentsPerPageForContentType.DoesNotExist:
        return getattr(settings, 'DEFAULT_COMMENTS_PER_PAGE', 100)

@register.simple_tag
def edit_comment_form_target():
    """
    Get the target URL for the comment form.

    Example::

        <form action="{% edit_comment_form_target %}" method="post">
    """
    return osl_comments.get_edit_form_target()
        
@register.tag
def get_anon_comment_form(parser, token):
    """
    Gets a form where the user can fill out their name, email, url, and comment
    
    Syntax::
        
        {% get_anon_comment_form for [object] as [varname] %}
        {% get_anon_comment_form for [app].[model] [object_id] as [varname] %}
        {% get_anon_comment_form for [object] replying to [parent_comment_id] as [varname] %}
        {% get_anon_comment_form for [app].[model] [object_id] replying to [parent_comment_id] as [varname] %}
    """
    return AnonOslCommentFormNode.handle_token(parser, token)
        
@register.tag
def get_comment_paginator_page(parser, token):
    """
    Gets a paginator for navigating through comment lists
    
    Syntax::
        
        {% get_comment_paginator_page for [object] as [varname] %}
        {% get_comment_paginator_page for [app].[model] [pk] as [varname] %}
    """
    
    tokens = token.contents.split()
    if tokens[1] != 'for':
        raise template.TemplateSyntaxError("First argument in %r tag must be 'for'" % tokens[0])
    if len(tokens) == 5:
        if tokens[3] != 'as':
            raise template.TemplateSyntaxError("Third argument in %r tag must be 'as'" % tokens[0])
        return CommentPaginationPageNode(
            object_expr = parser.compile_filter(tokens[2]),
            as_varname = tokens[4]
        )
    if len(tokens) == 6:
        if tokens[4] != 'as':
            raise template.TemplateSyntaxError("Fifth argument in %r tag must be 'as'" % tokens[0])
        return CommentPaginationPageNode(
            ctype = BaseCommentNode.lookup_content_type(tokens[2], tokens[0]),
            object_pk_expr = parser.compile_filter(tokens[3]),
            as_varname = tokens[5]
        )
    raise template.TemplateSyntaxError("%r tag requires 4 or 5 arguments" % tokens[0])
        
def get_comment_page(context):
    """Returns the current comment page."""
    try:
        page_num = int(context['request'].GET.get('comment_page', 1))
    except ValueError:
        page_num = 1
    if page_num < 1:
        page_num = 1
    return page_num
        
@register.tag
def get_edit_comment_form(parser, token):
    """
    Gets a form where the user can edit their own comment
    
    Syntax::
    
        {% get_edit_comment_form for [comment] as [varname] %}
    """
    return OslEditCommentFormNode.handle_token(parser, token)
        
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

@register.tag
def output_comment_edit_url(parser, token):
    """
    Output a URL to trigger an edit to this comment
    
    Syntax::
    
        {% output_comment_edit_url for [comment_object] %}
    """
    try:
        tag_name, ignore, comment_object = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError("%r tag requires two arguments" % tokens.contents.split[0])
    if ignore != 'for':
        raise template.TemplateSyntaxError("First argument in %r must be 'for'" % tokens.contents.split[0])
    return EditUrlNode(parser.compile_filter(comment_object))

@register.tag
def output_comment_reply_url(parser, token):
    """
    Output a URL to trigger a reply to this comment
    
    Syntax::
    
        {% output_comment_reply_url for [comment_object] %}
    """
    try:
        tag_name, ignore, comment_object = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError("%r tag requires two arguments" % tokens.contents.split[0])
    if ignore != 'for':
        raise template.TemplateSyntaxError("First argument in %r must be 'for'" % tokens.contents.split[0])
    return ReplyUrlNode(parser.compile_filter(comment_object))

@register.tag
def render_anon_comment_form(parser, token):
    """
    Render the anonymous comment form (as returned by ``{% render_comment_form %}``) through
    the ``comments/form.html`` template.

    Syntax::

        {% render_anon_comment_form for [object] %}
        {% render_anon_comment_form for [app].[model] [object_id] %}
    """
    return RenderAnonOslCommentFormNode.handle_token(parser, token)
    
@register.tag
def render_edit_comment_form(parser, token):
    """
    Render the edit comment form through the `comments/form.html` template.
    
    Syntax::
    
        {% render_edit_comment_form for [comment] %}
    """
    return RenderOslEditCommentNode.handle_token(parser, token)


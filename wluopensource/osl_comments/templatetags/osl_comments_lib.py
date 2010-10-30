import urlparse

from django import template
from django.conf import settings
from django.contrib import comments
from django.contrib.comments.templatetags.comments import (BaseCommentNode, 
    CommentFormNode, CommentListNode, RenderCommentFormNode, 
    RenderCommentListNode)
from django.core.paginator import Paginator
from django.template.loader import render_to_string
from django.utils.encoding import smart_unicode

import osl_comments
from osl_comments.forms import AnonOslCommentForm, AuthOslCommentForm, OslEditCommentForm
from osl_comments.models import (CommentsBannedFromIpAddress, 
    CommentsPerPageForContentType, OslComment)
from osl_comments.views import NO_PAGINATION_QUERY_STRING_KEY

register = template.Library()

EDIT_QUERY_STRING_KEY = 'edit_comment'
PAGE_QUERY_STRING_KEY = 'comment_page'
REPLY_QUERY_STRING_KEY = 'reply_to_comment'
SORT_BY_QUERY_STRING_KEY = 'sort_comments_by'

class AbstractIsFormPresentNode(template.Node):
    form_query_string_key = None
    
    def __init__(self, as_varname):
        self.as_varname = as_varname
    
    @classmethod
    def handle_token(cls, parser, token):
        tokens = token.contents.split()
        
        # {% is_form_present as [varname] %}
        if len(tokens) != 3:
            raise template.TemplateSyntaxError("%r tag requires 2 arguments" % tokens[0])
        if tokens[1] != 'as':
            raise template.TemplateSyntaxError("First argument in %r tag must be 'as'" % tokens[0])
        return cls(as_varname = tokens[2])
    
    def render(self, context):
        context[self.as_varname] = \
            context['request'].GET.get(self.form_query_string_key, False)
        return ''
        
class AbstractPaginationUrlNode(template.Node):
    
    def __init__(self, page):
        self.page = page
    
    @classmethod
    def handle_token(cls, parser, token):
        tokens = token.contents.split()
        
        # {% output_something_comment_page_url with page %}
        if len(tokens) != 3:
            raise template.TemplateSyntaxError("%r tag requires 2 arguments" % tokens[0])
        if tokens[1] != 'with':
            raise template.TemplateSyntaxError("First argument for %r tag must be 'with'" % tokens[0])
        return cls(page = parser.compile_filter(tokens[2]))
        
class AbstractShouldDisplayFormNode(template.Node):
    query_string_key = None

    def __init__(self, comment, as_varname):
        self.comment = comment
        self.as_varname = as_varname
    
    @classmethod
    def handle_token(cls, parser, token):
        tokens = token.contents.split()
        
        # {% should_display_form for [comment] as [varname] %}
        if len(tokens) != 5:
            raise template.TemplateSyntaxError("%r tag requires 4 arguments" % tokens[0])
        if tokens[1] != 'for':
            raise template.TemplateSyntaxError("First argument in %r tag must be 'for'" % tokens[0])
        if tokens[3] != 'as':
            raise template.TemplateSyntaxError("Third argument in %r tag must be 'as'" % tokens[0])
        return cls(
            comment = parser.compile_filter(tokens[2]),
            as_varname = tokens[4]
        )
    
    def render(self, context):
        comment = self.comment.resolve(context)
        context[self.as_varname] = \
            context['request'].GET.get(self.query_string_key) == str(comment.id)
        return ''

class AbstractSortByUrlNode(template.Node):
    sort_by_value = None
    
    @classmethod
    def handle_token(cls, parser, token):
        tokens = token.contents.split()
        
        # {% get_sort_by_url as [varname] %}
        if len(tokens) != 1:
            raise template.TemplateSyntaxError("%r tag requires 0 arguments" % tokens[0])
        return cls()
        
    def render(self, context):
        return ''.join(['?', SORT_BY_QUERY_STRING_KEY, '=', self.sort_by_value])

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
        if EDIT_QUERY_STRING_KEY in query_string:
            del query_string[EDIT_QUERY_STRING_KEY]
        if REPLY_QUERY_STRING_KEY in query_string:
            del query_string[REPLY_QUERY_STRING_KEY]
        query_string[self.query_string_key] = comment.id
        return ''.join(['?', query_string.urlencode(), '#c', str(comment.id)])

class AnonOslCommentFormNode(CommentFormNode):
    
    def __init__(self, ctype=None, object_pk_expr=None, object_expr=None, 
        as_varname=None, comment=None, parent_comment=None):
        
        super(AnonOslCommentFormNode, self).__init__(ctype=ctype, 
            object_pk_expr=object_pk_expr, object_expr=object_expr, 
            as_varname=as_varname, comment=comment)
        self.parent_comment = parent_comment
    
    def get_form(self, context):
        ctype, object_pk = self.get_target_ctype_pk(context)
        if self.parent_comment is not None:
            parent_comment_id = self.parent_comment.resolve(context).id
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
        
        # {% get_anon_comment_form for obj replying to parent_comment as varname %}
        if len(tokens) == 8:
            if tokens[3] != 'replying':
                raise template.TemplateSyntaxError("Third argument in %r tag must be 'replying'" % tokens[0])
            if tokens[4] != 'to':
                raise template.TemplateSyntaxError("Fourth argument in %r tag must be 'to'" % tokens[0])
            if tokens[6] != 'as':
                raise template.TemplateSyntaxError("Sixth argument in %r tag must be 'as'" % tokens[0])
            return cls(
                object_expr = parser.compile_filter(tokens[2]),
                parent_comment = parser.compile_filter(tokens[5]),
                as_varname = tokens[7]
            )
            
        # {% get_anon_comment_form for app.model pk replying to parent_comment as varname %}
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
                parent_comment = parser.compile_filter(tokens[6]),
                as_varname = tokens[8]
            )
        
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
            is_public = True,
            inline_to_object = False
        )

        if is_paginated(context):
            comment_paginator = Paginator(comment_list, 
                CommentsPerPageForContentType.objects.get_comments_per_page_for_content_type(
                ctype))
        else:
            comment_paginator = Paginator(comment_list, len(comment_list))
            
        context[self.as_varname] = comment_paginator.page(
            get_comment_page(context))
        return ''

class EditUrlNode(AbstractUrlNode):
    query_string_key = EDIT_QUERY_STRING_KEY
    type_of_object = 'Edit'
    
class IsEditFormPresentNode(AbstractIsFormPresentNode):
    """Insert whether an edit form is displayed somewhere into the context."""
    form_query_string_key = EDIT_QUERY_STRING_KEY
    
class IsReplyFormPresentNode(AbstractIsFormPresentNode):
    """Insert whether a reply form is displayed somewhere into the context."""
    form_query_string_key = REPLY_QUERY_STRING_KEY
    
class NextPageUrlNode(AbstractPaginationUrlNode):
    """Output URL to get next page of comments."""
    
    def render(self, context):
        page = self.page.resolve(context)
        query_string = context['request'].GET.copy()
        if EDIT_QUERY_STRING_KEY in query_string:
            del query_string[EDIT_QUERY_STRING_KEY]
        if REPLY_QUERY_STRING_KEY in query_string:
            del query_string[REPLY_QUERY_STRING_KEY]
        query_string[PAGE_QUERY_STRING_KEY] = str(page.next_page_number())
        return ''.join(['?', query_string.urlencode()])

class OslCommentListNode(CommentListNode):
    """Insert a list of comments into the context."""
    
    def get_query_set(self, context):
        ctype, object_pk = self.get_target_ctype_pk(context)
        if not object_pk:
            return self.comment_model.objects.none()
        
        sorted_by = context['request'].GET.get(SORT_BY_QUERY_STRING_KEY)
        
        if sorted_by == SortByNewestUrlNode.sort_by_value:
            order_method = 'latest'
        elif sorted_by == SortByScoreUrlNode.sort_by_value:
            order_method = 'score'
        elif sorted_by == SortByOldestUrlNode.sort_by_value:
            order_method = 'oldest'
        else:
            order_method = 'latest'
            
        qs = self.comment_model.objects.get_comments(ctype, object_pk,
            sorted_by, is_paginated(context), get_comment_page(context))

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

        else:
            raise template.TemplateSyntaxError("%r tag requires 4 or 5 arguments" % tokens[0])
            
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

class PreviousPageUrlNode(AbstractPaginationUrlNode):
    """Output URL to get previous page of comments."""
    
    def render(self, context):
        page = self.page.resolve(context)
        query_string = context['request'].GET.copy()
        if EDIT_QUERY_STRING_KEY in query_string:
            del query_string[EDIT_QUERY_STRING_KEY]
        if REPLY_QUERY_STRING_KEY in query_string:
            del query_string[REPLY_QUERY_STRING_KEY]
        query_string[PAGE_QUERY_STRING_KEY] = str(page.previous_page_number())
        return ''.join(['?', query_string.urlencode()])

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
        
        # {% render_anon_comment_form for obj replying to parent_comment %}
        if len(tokens) == 6:
            if tokens[3] != 'replying':
                raise template.TemplateSyntaxError("Third argument in %r tag must be 'replying'" % tokens[0])
            if tokens[4] != 'to':
                raise template.TemplateSyntaxError("Fourth argument in %r tag must be 'to'" % tokens[0])
            return cls(
                object_expr = parser.compile_filter(tokens[2]),
                parent_comment = parser.compile_filter(tokens[5])
            )
            
        # {% render_anon_comment_form for app.model pk replying to parent_comment %}
        if len(tokens) == 7:
            if tokens[4] != 'replying':
                raise template.TemplateSyntaxError("Fourth argument in %r tag must be 'replying'" % tokens[0])
            if tokens[5] != 'to':
                raise template.TemplateSyntaxError("Fifth argument in %r tag must be 'to'" % tokens[0])
            return cls(
                ctype = BaseCommentNode.lookup_content_type(tokens[2], tokens[0]),
                object_pk_expr = parser.compile_filter(tokens[3]),
                parent_comment = parser.compile_filter(tokens[6])
            )

        raise template.TemplateSyntaxError("%r tag requires 2, 3, 5, or 6 arguments" % tokens[0])
        
class RenderOslCommentListNode(OslCommentListNode):
    """Render the comment list directly"""
    
    def __init__(self, ctype=None, object_pk_expr=None, object_expr=None, 
        as_varname=None, comment=None, comments_enabled=None):
    
        super(RenderOslCommentListNode, self).__init__(ctype=ctype, 
            object_pk_expr=object_pk_expr, object_expr=object_expr, 
            as_varname=as_varname, comment=comment)
            
        self.comments_enabled = comments_enabled

    @classmethod
    def handle_token(cls, parser, token):
        tokens = token.contents.split()
        if tokens[1] != 'for':
            raise template.TemplateSyntaxError("First argument in %r tag must be 'for'" % tokens[0])
        
        # {% render_threaded_comment_list for obj with comments comments_enabled_field %}
        if len(tokens) == 6:
            if tokens[3] != 'with':
                raise template.TemplateSyntaxError("Third argument in %r tag must be 'with'" % tokens[0])
            if tokens[4] != 'comments':
                raise template.TemplateSyntaxError("Fourth argument in %r tag must be 'comments'" % tokens[0])
            return cls(
                object_expr = parser.compile_filter(tokens[2]),
                comments_enabled = parser.compile_filter(tokens[5])
            )
        
        # {% render_threaded_comment_list for app.model pk with comments comments_enabled_field %}
        if len(tokens) == 7:
            if tokens[4] != 'with':
                raise template.TemplateSyntaxError("Fourth argument in %r tag must be 'with'" % tokens[0])
            if tokens[5] != 'comments':
                raise template.TemplateSyntaxError("Fifth argument in %r tag must be 'comments'" % tokens[0])
            return cls(
                ctype = BaseCommentNode.lookup_content_type(tokens[2], tokens[0]),
                object_pk_expr = parser.compile_filter(tokens[3]),
                comments_enabled = parser.compile_filter(tokens[6])
            )
            
        raise template.TemplateSyntaxError("%r tags takes 5 or 6 arguments" % tokens[0])
        
    def render(self, context):
        ctype, object_pk = self.get_target_ctype_pk(context)
        if object_pk:
            template_search_list = [
                "comments/%s/%s/list.html" % (ctype.app_label, ctype.model),
                "comments/%s/list.html" % ctype.app_label,
                "comments/list.html"
            ]
            qs = self.get_query_set(context)
            context.push()
            liststr = render_to_string(template_search_list, {
                "comment_list" : self.get_context_value_from_queryset(context, qs),
                "comments_enabled" : self.comments_enabled.resolve(context),
                "object": self.object_expr.resolve(context)
            }, context)
            context.pop()
            return liststr
        else:
            return ''
        
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
    query_string_key = REPLY_QUERY_STRING_KEY
    type_of_object = 'Reply'
    
class ShouldDisplayEditFormNode(AbstractShouldDisplayFormNode):
    """
    Insert whether an edit form should be displayed for the specified content 
    into the context.
    """
    query_string_key = EDIT_QUERY_STRING_KEY
    
class ShouldDisplayReplyFormNode(AbstractShouldDisplayFormNode):
    """
    Insert whether a reply form should be displayed for the specified content 
    into the context.
    """
    query_string_key = REPLY_QUERY_STRING_KEY
    
    def render(self, context):
        super(ShouldDisplayReplyFormNode, self).render(context)
        comment = self.comment.resolve(context)
        if context[self.as_varname] and not comment.parent:
            context[self.as_varname] = False
        return ''
        
class SortByNewestUrlNode(AbstractSortByUrlNode):
    sort_by_value = 'newest'
    
class SortByOldestUrlNode(AbstractSortByUrlNode):
    sort_by_value = 'oldest'
    
class SortByScoreUrlNode(AbstractSortByUrlNode):
    sort_by_value = 'score'
        
class UserIsBannedNode(template.Node):
    """Insert whether the current user is banned from commenting."""
    
    def __init__(self, as_varname):
        self.as_varname = as_varname
        
    @classmethod
    def handle_token(cls, parser, token):
        tokens = token.contents.split()
        
        # {% user_is_banned_from_commenting_node as varname %}
        if len(tokens) != 3:
            raise template.TemplateSyntaxError("%r tag takes 2 arguments" % tokens[0])
        if tokens[1] != 'as':
            raise template.TemplateSyntaxError("First argument in %r tag must be 'for'" % tokens[0])
        return cls(as_varname = tokens[2])
    
    def render(self, context):
        user_ip_address = context['request'].META['REMOTE_ADDR']
        user_is_banned = False
        try:
            user_is_banned = \
                CommentsBannedFromIpAddress.objects.get(
                ip_address = user_ip_address).comments_banned
        except CommentsBannedFromIpAddress.DoesNotExist:
            user_is_banned = False
        finally:
            context[self.as_varname] = user_is_banned
            return ''

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
        {% get_anon_comment_form for [object] replying to [parent_comment] as [varname] %}
        {% get_anon_comment_form for [app].[model] [object_id] replying to [parent_comment] as [varname] %}
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
def is_edit_form_present(parser, token):
    """
    Gets whether or not an edit form is present.
    
    Syntax::
    
        {% is_edit_form_present as [varname] %}
    """
    return IsEditFormPresentNode.handle_token(parser, token)
    
def is_paginated(context):
    """Gets whether or not the page should be paginated."""
    
    # Check to make sure referring page is from same domain (should paginate
    # if referring domain is different since don't want search engines pointing
    # to non-paginated comments)
    referer = context['request'].META.get('HTTP_REFERER', None)
    current_url = context['request'].build_absolute_uri()
    no_pagination = \
        context['request'].GET.get(NO_PAGINATION_QUERY_STRING_KEY, False)
        
    return not (referer and 
        urlparse.urlparse(referer)[1] == urlparse.urlparse(current_url)[1] and 
        no_pagination)
    
@register.tag
def is_reply_form_present(parser, token):
    """
    Gets whether or not a reply form is present.
    
    Syntax::
    
        {% is_reply_form_present as [varname] %}
    """
    return IsReplyFormPresentNode.handle_token(parser, token)

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
def output_next_comment_page_url(parser, token):
    """
    Output the URL to get the next page of comments.
    
    Syntax::
    
        {% output_next_comment_page_url with [page_object] %}
    """
    return NextPageUrlNode.handle_token(parser, token)

@register.tag
def output_previous_comment_page_url(parser, token):
    """
    Output the URL to get the previous page of comments.
    
    Syntax::
    
        {% output_previous_comment_page_url with [page_object] %}
    """
    return PreviousPageUrlNode.handle_token(parser, token)

@register.tag
def output_sort_by_newest_url(parser, token):
    """
    Output the URL to sort the comments by descending date
    
    Syntax::
        
        {% output_sort_by_newest_url %}
    """
    return SortByNewestUrlNode.handle_token(parser, token)
    
@register.tag
def output_sort_by_oldest_url(parser, token):
    """
    Output the URL to sort the comments by ascending date
    
    Syntax::
        
        {% output_sort_by_oldest_url %}
    """
    return SortByOldestUrlNode.handle_token(parser, token)
    
@register.tag
def output_sort_by_score_url(parser, token):
    """
    Output the URL to sort the comments by descending score
    
    Syntax::
    
        {% output_sort_by_score_url %}
    """
    return SortByScoreUrlNode.handle_token(parser, token)

@register.tag
def render_anon_comment_form(parser, token):
    """
    Render the anonymous comment form (as returned by ``{% render_comment_form %}``) through
    the ``comments/form.html`` template.

    Syntax::

        {% render_anon_comment_form for [object] %}
        {% render_anon_comment_form for [app].[model] [pk] %}
        {% render_anon_comment_form for [object] replying to [comment] %}
        {% render_anon_comment_form for [app].[model] [pk] replying to [comment] %}
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

@register.tag
def render_threaded_comment_list(parser, token):
    """
    Renders the list of comments for the given params.

    Syntax::

        {% render_threaded_comment_list for [object] with comments [comments_enabled_field] %}
        {% render_threaded_comment_list for [app].[model] [object_id] with comments [comments_enabled_field] %}
        {% render_threaded_comment_list for [object] sorted by [column] with comments [comments_enabled_field] %}
        {% render_threaded_comment_list for [app].[model] [object_id] sorted by [column] with comments [comments_enabled_field] %}
    """
    return RenderOslCommentListNode.handle_token(parser, token)

@register.tag
def should_display_edit_form(parser, token):
    """
    Gets whether an edit form should be displayed for the given comment.
    
    Syntax::
    
        {% should_display_edit_form for [comment] as [varname]
    """
    return ShouldDisplayEditFormNode.handle_token(parser, token)

@register.tag
def should_display_reply_form(parser, token):
    """
    Gets whether a reply form should be displayed for the given comment.
    
    Syntax::
    
        {% should_display_reply_form for [comment] as [varname] %}
    """
    return ShouldDisplayReplyFormNode.handle_token(parser, token)
    
@register.tag
def user_is_banned_from_commenting(parser, token):
    """
    Gets whether the current user is banned from commenting.
    
    Syntax::
    
        {% user_is_banned_from_commenting as [varname] %}
    """
    return UserIsBannedNode.handle_token(parser, token)


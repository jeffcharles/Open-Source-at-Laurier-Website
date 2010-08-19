from django.contrib.comments.templatetags import CommentListNode


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
        
        if self.sorted_by = 'oldest':
            order_by = 'submit_date ASC'
        elif self.sorted_by = 'newest':
            order_by = 'submit_date DESC'
        else:
            order_by = 'submit_date DESC'
        
        sql = """
            SELECT
                dc.user_name,
                dc.user_url,
                dc.comment,
                dc.submit_date,
                oc.edit_timestamp
                dc2.user_name,
                dc2.user_url,
                dc2.comment,
                dc2.submit_date,
                oc2.edit_timestamp
            FROM
                django_comments AS dc
            JOIN
                osl_comments_oslcomments AS oc 
                ON dc.id = oc.comment_ptr_id 
            LEFT OUTER JOIN
                osl_comments_oslcomments AS oc2 
                ON oc.comment_ptr_id = oc2.parent_comment_pk 
            JOIN
                django_comments AS dc2 
                ON oc2.comment_ptr_id = dc2.id
            WHERE
                dc.content_type_id = %(content_type)r AND
                dc.object_pk = %(object_pk)r AND
                dc.site_id = %(site_id)r AND
                ((dc.is_public = True AND dc2.id = NULL) OR dc2.is_public = True) AND
                dc.inline_to_object = False
            ORDER BY
                dc.%(first_thread_order_by)r,
                dc.id ASC
                dc2.%(second_thread_order_by)r
            LIMIT
                %(limit)r
            OFFSET
                %(offset)r
        """ % {
            'content_type': ctype,
            'object_pk': smart_unicode(object_pk),
            'site_id': settings.SITE_ID,
            'first_thread_order_by': order_by,
            'second_thread_order_by': order_by,
            'limit': self.limit, 
            'offset': self.offset
        }
        
        qs = self.comment_model.objects.raw(sql)

        field_names = [f.name for f in self.comment_model._meta.fields]
        if getattr(settings, 'COMMENTS_HIDE_REMOVED', True) and 'is_removed' in field_names:
            qs = qs.filter(is_removed=False)

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
                limit = tokens[6],
                offset = tokens[8]
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
                ctype = OslBaseCommentNode.lookup_content_type(tokens[2], tokens[0]),
                object_pk_expr = parser.compile_filter(tokens[3]),
                as_varname = tokens[5],
                limit = tokens[7],
                offset = tokens[9]
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
                object_expr = parser.complile_filter(tokens[2]),
                as_varname = tokens[4],
                sorted_by = tokens[7],
                limit = tokens[9],
                offset = tokens[11]
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
                ctype = OslBaseCommentNode.lookup_content_type(tokens[2], tokens[0]),
                object_pk_expr = parser.compile_filter(tokens[3]),
                as_varname = tokens[5],
                sorted_by = tokens[8],
                limit = tokens[10],
                offset = tokens[11]
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

        {% get_comment_list for [object] as [varname]  %}
        {% get_comment_list for [app].[model] [object_id] as [varname]  %}
        {% get_comment_list for [object] as [varname] sorted by [column] %}
        {% get_comment_list for [app].[model] [object_id] as [varname] sorted by [column] %}

    Example usage::

        {% get_comment_list for event as comment_list %}
        {% for comment in comment_list %}
            ...
        {% endfor %}

    """
    return CommentListNode.handle_token(parser, token)


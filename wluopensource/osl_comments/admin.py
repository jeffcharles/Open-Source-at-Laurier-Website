from django.contrib import admin
from django.contrib.comments.admin import CommentsAdmin
from django.contrib.comments.models import CommentFlag

from osl_comments.models import (CommentsBannedFromIpAddress, 
    CommentsPerPageForContentType, OslComment)

class CommentFlagAdmin(admin.ModelAdmin):
    pass
admin.site.register(CommentFlag, CommentFlagAdmin)

class CommentsBannedFromIpAddressAdmin(admin.ModelAdmin):
    pass
admin.site.register(CommentsBannedFromIpAddress,
    CommentsBannedFromIpAddressAdmin)

class CommentsPerPageForContentTypeAdmin(admin.ModelAdmin):
    pass
admin.site.register(CommentsPerPageForContentType, 
    CommentsPerPageForContentTypeAdmin)

class OslCommentsAdmin(CommentsAdmin):
    fieldsets = (
        (None,
           {'fields': ('content_type', 'object_pk', 'site')}
        ),
        ('Content',
           {'fields': ('user', 'user_name', 'user_email', 'user_url', 'parent_comment', 'comment')}
        ),
        ('Metadata',
           {'fields': ('submit_date', 'edit_timestamp', 'ip_address', 'is_public', 'is_removed')}
        ),
    )
    
    list_display = ('name', 'content_type', 'object_pk', 'ip_address', 
        'submit_date', 'is_public', 'is_removed', 'is_flagged')
admin.site.register(OslComment, OslCommentsAdmin)


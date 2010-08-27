from django.contrib import admin
from django.contrib.comments.admin import CommentsAdmin

from osl_comments.models import OslComment

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
admin.site.register(OslComment, OslCommentsAdmin)


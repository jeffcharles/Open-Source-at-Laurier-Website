from django.contrib import comments
from django.contrib.comments.moderation import CommentModerator, Moderator
from django.core.exceptions import ObjectDoesNotExist

from osl_comments import signals
from osl_comments.models import CommentsBannedFromIpAddress

class OslCommentModerator(CommentModerator):
    email_notification = True
    enable_field = 'enable_comments'
    
    def allow(self, comment, content_object, request):
        """
        Determine whether a given comment is allowed to be posted on
        a given object.

        Return ``True`` if the comment should be allowed, ``False
        otherwise.
        """
        allowed = \
            super(OslCommentModerator, self).allow(comment, content_object, 
            request)
        
        if not allowed:
            return False
        else:
            comment_banned_from_ip = False
            try:
                comment_banned_from_ip = \
                    CommentsBannedFromIpAddress.objects.get(
                    ip_address=comment.ip_address).comments_banned
            except ObjectDoesNotExist:
                comment_banned_from_ip = False
            finally:
                comment_allowed_from_ip = not comment_banned_from_ip
                return comment_allowed_from_ip

class OslModerator(Moderator):
    """Registers editing alongside posting signals with the moderator."""
    
    def connect(self):
        super(OslModerator, self).connect()
        signals.comment_will_be_edited.connect(self.pre_save_moderation, 
            sender=comments.get_model())
        signals.comment_was_edited.connect(self.post_save_moderation, 
            sender=comments.get_model())
            
moderator = OslModerator()


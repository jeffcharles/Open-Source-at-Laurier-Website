from datetime import datetime

from django.contrib.comments.views import comments
from django.contrib.comments.views.comments import CommentPostBadRequest
from django.contrib.comments.views.utils import confirmation_view, next_redirect
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST

from osl_comments.forms import OslEditCommentForm
from osl_comments.models import OslComment

@require_POST
def edit_comment(request, next=None):
    # get data
    data = request.POST.copy()
    next = data.get('next', next)
    
    # get comment and raise error if id is wrong
    comment_id = data.get('comment_id')
    if comment_id is None:
        return CommentPostBadRequest("Missing comment id field.")
    try:
        comment = OslComment.objects.get(pk=comment_id)
    except ObjectDoesNotExist:
        return CommentPostBadRequest(
            "No comment matching with PK %r exists." % comment_id
        )
    except (ValueError, ValidationError) as e:
        return CommentPostBadRequest(
            "Attempting to get comment PK %r raised %s" % 
            (escape(comment_id), e.__class__.__name__)
        )
    
    # ensure user editing is same user who posted comment
    if comment.user != request.user:
        return CommentPostBadRequest("Cannot edit another user's comment.")
    
    # does the user want to preview the comment?
    preview = 'preview' in data
    
    # get a special comment form for editing
    form = OslEditCommentForm(data=data)
    
    # If there are errors or if we requested a preview show the comment
    if form.errors or preview:
        template_list = [
            # These first two exist for purely historical reasons.
            # Django v1.0 and v1.1 allowed the underscore format for
            # preview templates, so we have to preserve that format.
            "comments/%s_%s_preview.html" % (comment.content_type.app_label, comment.content_type.model),
            "comments/%s_preview.html" % comment.content_type.app_label,
            # Now the usual directory based template heirarchy.
            "comments/%s/%s/preview.html" % (comment.content_type.app_label, comment.content_type.model),
            "comments/%s/preview.html" % comment.content_type.app_label,
            "comments/preview.html",
        ]
        return render_to_response(
            template_list, {
                "comment" : form.data.get("comment", ""),
                "form" : form,
                "next": next,
            },
            RequestContext(request, {})
        )
        
    # update comment content
    comment.comment = data.get('comment')
    comment.edit_timestamp = datetime.now()
    comment.save()
    
    return next_redirect(data, next, comment_edited, c=comment._get_pk_val())

comment_edited = confirmation_view(
    template = "comments/edit_confirmed.html",
    doc = """Display a "comment was edited" success page."""
)
    

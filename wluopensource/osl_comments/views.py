from datetime import datetime
import urllib
import urlparse

from django.conf import settings
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import comments as comment_app
from django.contrib.comments.views import comments
from django.contrib.comments.views.comments import CommentPostBadRequest
from django.contrib.comments.views.utils import confirmation_view, next_redirect
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.http import HttpResponseBadRequest, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render_to_response
from django.template import RequestContext, loader
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST

from osl_comments import signals
from osl_comments.forms import OslEditCommentForm
from osl_comments.models import CommentsBannedFromIpAddress, OslComment

NO_PAGINATION_QUERY_STRING_KEY = 'np'

@login_required
def delete_comment(request, comment_id, next=None):
    """
    Deletes a comment. Confirmation on GET, action on POST.
    
    Templates: `comments/delete_by_user.html`, 
               `comments/delete_by_user_forbidden.html`
    Context:
        comment
            the deleted `comments.comment` object
    """
    comment = get_object_or_404(comment_app.get_model(), pk=comment_id, 
        site__pk=settings.SITE_ID)
    
    # Ensure requesting user is same user who posted comment
    if request.user != comment.user:
        t = loader.get_template('comments/delete_by_user_forbidden.html')
        c = RequestContext(request)
        return HttpResponseForbidden(t.render(c))

    # Delete on POST
    if request.method == 'POST':
        comment.is_deleted_by_user = True
        comment.save()
        signals.comment_was_deleted_by_user.send(
            sender = comment.__class__,
            comment = comment,
            request = request
        )
        return next_redirect(request.POST.copy(), next, delete_by_user_done, 
            c=comment.pk)

    # Render a form on GET
    else:
        return render_to_response('comments/delete_by_user.html',
            {'comment': comment, "next": next},
            RequestContext(request)
        )
        
delete_by_user_done = confirmation_view(
    template = "comments/deleted_by_user.html",
    doc = 'Displays a "comment was deleted" success page.'
)

@login_required
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
        
    responses = signals.comment_will_be_edited.send(
        sender  = comment.__class__,
        comment = comment,
        request = request
    )
    
    for (receiver, response) in responses:
        if response == False:
            return CommentPostBadRequest(
                "comment_will_be_edited receiver %r killed the comment" % receiver.__name__)
        
    # update comment content
    comment.comment = data.get('comment')
    comment.edit_timestamp = datetime.now()
    comment.save()
    
    signals.comment_was_edited.send(
        sender  = comment.__class__,
        comment = comment,
        request = request
    )
    
    return next_redirect(data, next, comment_edited, c=comment._get_pk_val())

comment_edited = confirmation_view(
    template = "comments/edit_confirmed.html",
    doc = """Display a "comment was edited" success page."""
)

def redirect_view(request, content_type_id, object_id):
    """
    Used instead of standard comments-url-redirect view to allow for no 
    pagination.
    """
    from django.contrib.contenttypes.views import shortcut
    response = shortcut(request, content_type_id, object_id)
    original_url = response['location']
    
    # Add in no pagination query string key
    url_list = list(urlparse.urlparse(original_url))    
    url = url_list[:4]
    query_string = url_list[4]
    fragment = url_list[5]
    
    query_string_dict = urlparse.parse_qs(query_string)
    query_string_dict.update({NO_PAGINATION_QUERY_STRING_KEY: '1'})
    new_qs = urllib.urlencode(query_string_dict)
    
    url.extend([new_qs, fragment])
    url_string = urlparse.urlunparse(url)
    response['location'] = url_string
    return response

@login_required
@permission_required('osl_comments.can_ban')
def update_ip_address_ban(request, comment_id, next=None):
    try:
        comment = OslComment.objects.get(pk=comment_id)
    except OslComment.DoesNotExist:
        return HttpResponseBadRequest()
        
    if request.method == 'GET':
        try:    
            banned = \
                CommentsBannedFromIpAddress.objects.get(
                ip_address=comment.ip_address).comments_banned
        except CommentsBannedFromIpAddress.DoesNotExist:
            banned = False
        return render_to_response('comments/update_ip_address_ban.html',
            {'banned': banned},
            RequestContext(request)
        )
    
    if request.method == 'POST':
        data = request.POST
        banned_str = data.get('ban', None)
        if banned_str == 'True':
            banned = True
        elif banned_str == 'False':
            banned = False
        else:
            return HttpResponseBadRequest()
        
        try:
            ban = CommentsBannedFromIpAddress.objects.get(
                ip_address=comment.ip_address)
        except CommentsBannedFromIpAddress.DoesNotExist:
            ban = CommentsBannedFromIpAddress(ip_address=comment.ip_address)
        ban.comments_banned = banned
        ban.save()
        
        signals.ip_address_ban_was_updated.send(
            sender = comment.__class__,
            banned = banned,
            request = request
        )
        
        return next_redirect(request.POST.copy(), next, 
            update_ip_address_ban_done)
            
update_ip_address_ban_done = confirmation_view(
    template = "comments/update_ip_address_ban_done.html",
    doc = """Display a "ip address ban updated" success page."""
)
    

from datetime import datetime
import urllib
import urlparse

from django.conf import settings
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import comments as comment_app
from django.contrib.comments.views import comments
from django.contrib.comments.views.comments import CommentPostBadRequest, comment_done
from django.contrib.comments.views.utils import confirmation_view, next_redirect
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.http import (HttpResponse, HttpResponseBadRequest, 
    HttpResponseForbidden)
from django.shortcuts import get_object_or_404, redirect, render_to_response
from django.template import RequestContext, loader
from django.utils.encoding import smart_unicode
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST

from osl_comments import signals
from osl_comments.forms import OslEditCommentForm
from osl_comments.models import (CommentsBannedFromIpAddress, 
    CommentsPerPageForContentType, OslComment)
from osl_comments.templatetags import (EDIT_QUERY_STRING_KEY, 
    REPLY_QUERY_STRING_KEY)

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
        if request.is_ajax():
            return redirect('osl_comments.views.get_comment', 
                comment_id=comment_id)
        else:
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
    
    # see if user wants to cancel
    cancel = 'cancel' in data
    if cancel:
        return redirect(data['cancel_url'])
    
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
    
    if request.is_ajax():
        return redirect('osl_comments.views.get_comment', comment_id=comment.pk)
    else:
        return next_redirect(data, next, comment_edited)

comment_edited = confirmation_view(
    template = "comments/edit_confirmed.html",
    doc = """Display a "comment was edited" success page."""
)

@require_POST
@login_required
def flag(request, comment_id, next=None):
    if not request.is_ajax:
        return redirect('django.contrib.comments.views.moderation.flag', 
            comment_id)
            
    from django.contrib.comment.views.moderation import perform_flag
    comment = get_object_or_404(OslComment, pk=comment_id, 
        site__pk=settings.SITE_ID)
    perform_flag(request, comment)
    
    return HttpResponse(status=200)

def get_ajax_edit_form(request, comment_pk):
    comment = OslComment.objects.get(pk=comment_pk)
    return render_to_response(
        "comments/render_edit_form.html",
        {'comment': comment},
        RequestContext(request)
    )

def get_ajax_reply_form(request, obj_ctype_pk, obj_pk, comment_pk):
    obj_model = ContentType.objects.get(pk=obj_ctype_pk).model_class()
    obj = obj_model.objects.get(pk=obj_pk)
    comment = OslComment.objects.get(pk=comment_pk)
    return render_to_response(
        "comments/reply_form_container.html",
        {'object': obj, 'comment': comment},
        RequestContext(request)
    )

def get_comment(request, comment_id):
    comment = get_object_or_404(OslComment, pk=comment_id)
    return render_to_response('comments/comment.html',
        {'comment': comment, 'comments_enabled': True, 
        'comment_parent': comment.parent_comment == None}, 
        context_instance=RequestContext(request))

def load_more(request, obj_ctype_pk, obj_pk, order_method, page_to_load):
    """Renders a list of comments."""
    
    page_to_load = int(page_to_load)
    
    obj_ctype = ContentType.objects.get(pk=obj_ctype_pk)
    
    comment_list = list(OslComment.objects.get_comments(obj_ctype, obj_pk, 
        order_method, True, page_to_load))
    
    comment_count = OslComment.objects.filter(
            content_type = obj_ctype,
            object_pk = smart_unicode(obj_pk),
            site__pk = settings.SITE_ID,
            is_public = True,
            inline_to_object = False
        ).count()
    num_comments_per_page = CommentsPerPageForContentType.objects.get_comments_per_page_for_content_type(
        obj_ctype)
    display_load_more = False
    if num_comments_per_page * page_to_load < comment_count:
        display_load_more = True
    
    return render_to_response(
        'comments/inner_list.html', 
        {
            'comment_list': comment_list, 
            'display_load_more': display_load_more,
            'sorted_by': order_method, 
            'object_ctype_pk': obj_ctype_pk, 
            'object_pk': obj_pk, 
            'next_comment_page': page_to_load + 1
        },
        RequestContext(request)
    )

@require_POST
@permission_required('comments.can_moderate')
def moderate(request, comment_id, next=None):
    if not request.is_ajax:
        return redirect('django.contrib.comments.views.moderation.delete', 
            comment_id)
        
    from django.contrib.comments.views.moderation import perform_delete
    comment = get_object_or_404(OslComment, pk=comment_id, 
        site__pk=settings.SITE_ID)
    perform_delete(request, comment)
    
    return redirect('osl_comments.views.get_comment', comment_id=comment_id)

@csrf_protect
@require_POST
def post_comment(request, next=None, using=None):
    """Wraps Django's post_comment view to handle the redirect better."""
    data = request.POST.copy()
    if 'cancel' in data:
        return redirect(data['cancel_url'])
    
    response = comments.post_comment(request, next, using)
    
    if response.status_code == 302:
        # Move the comment pk in the query string to the URL fragment 
        # (and clear out delete and reply key values pairs as well)
        redirect_location = response['location']
        redirect_url = list(urlparse.urlparse(redirect_location))
        redirect_qs = urlparse.parse_qs(redirect_url[4])
        comment_pk = ''
        if 'c' in redirect_qs:
            comment_pk = redirect_qs['c'][0]
            del redirect_qs['c']
        if EDIT_QUERY_STRING_KEY in redirect_qs:
            del redirect_qs[EDIT_QUERY_STRING_KEY]
        if REPLY_QUERY_STRING_KEY in redirect_qs:
            del redirect_qs[REPLY_QUERY_STRING_KEY]
        redirect_url[4] = urllib.urlencode(redirect_qs, True)
        redirect_url[5] = ''.join(['c', comment_pk])
        response['location'] = urlparse.urlunparse(redirect_url)
    
    return response

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
    

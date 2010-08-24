from django.contrib.comments.views import comments
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST

@csrf_protect
@require_POST
def post_comment(request, next=None, using=None):
    request.flash['comment_response'] = 'Your comment has been added!'
    return comments.post_comment(request, next, using)
    

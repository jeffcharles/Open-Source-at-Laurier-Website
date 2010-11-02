from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response
from django.utils import simplejson

from voting.models import Vote

def get_vote_box_template(request, object_id, model, vote_url_name):
    
    lookup_kwargs = {}
    lookup_kwargs['%s__exact' % model._meta.pk.name] = object_id
    try:
        obj = model._default_manager.get(**lookup_kwargs)
    except ObjectDoesNotExist:
        return HttpResponse(simplejson.dumps(dict(success=False,
            error_message='No %s found for %s.' % (model._meta.verbose_name, 
            lookup_kwargs))))
    
    vote = Vote.objects.get_for_user(obj, request.user)
    upvote_url = \
        reverse(vote_url_name, kwargs={'object_id': object_id, 'direction': 'up'})
    clearvote_url = \
        reverse(vote_url_name, kwargs={'object_id': object_id, 
        'direction': 'clear'})
    downvote_url = \
        reverse(vote_url_name, kwargs={'object_id': object_id, 
        'direction': 'down'})
    
    return render_to_response('voting/default_vote_box.html', 
        {'vote': vote, 'upvote_url': upvote_url, 'clearvote_url': clearvote_url,
        'downvote_url': downvote_url})


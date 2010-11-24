from django.contrib.comments.signals import comment_was_posted

from voting.models import Vote

def auto_upvote_self_posts(sender, **kwargs):
    if 'request' in kwargs and 'comment' in kwargs:
        request = kwargs['request']
        comment = kwargs['comment']
        
        if request.user.is_authenticated():
            Vote.objects.record_vote(comment, request.user, 1)
comment_was_posted.connect(auto_upvote_self_posts)


from django.conf.urls.defaults import *
from django.contrib.comments.urls import urlpatterns

from osl_comments.models import OslComment

urlpatterns += patterns('osl_comments.views',
    (r'^delete_comment/(?P<comment_id>\d+)/$', 'delete_comment'),
    (r'^deleted_comment/$', 'delete_by_user_done'),
    (r'^edit/$', 'edit_comment'),
    (r'^edited/$', 'comment_edited'),
    (r'^ip_address_ban/(?P<comment_id>\d+)/$', 'update_ip_address_ban'),
    (r'^ip_address_ban_update_done/$', 'update_ip_address_ban_done'),
    url(r'^ocr/(\d+)/(.+)/$', 'redirect_view', name='osl-comments-url-redirect'),
    
)

comment_voting_dict = {'model': OslComment, 'template_object_name': 'comment', 
    'allow_xmlhttprequest': True}

comment_clear_voting_dict = comment_voting_dict.copy()
comment_clear_voting_dict.update({'direction': 'clear'})

comment_down_voting_dict = comment_voting_dict.copy()
comment_down_voting_dict.update({'direction': 'down'})

comment_up_voting_dict = comment_voting_dict.copy()
comment_up_voting_dict.update({'direction': 'up'})

urlpatterns += patterns('voting.views',
    url(r'^vote/(?P<object_id>\d+)/clear/$', 'vote_on_object', 
        comment_clear_voting_dict, name='vote-comment-clear'),
    url(r'^vote/(?P<object_id>\d+)/down/$', 'vote_on_object', 
        comment_down_voting_dict, name='vote-comment-down'),
    url(r'^vote/(?P<object_id>\d+)/up/$', 'vote_on_object', 
        comment_up_voting_dict, name='vote-comment-up'),
)


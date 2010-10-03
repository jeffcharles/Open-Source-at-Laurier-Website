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

urlpatterns += patterns('voting.views',
    url(r'^vote/(?P<object_id>\d+)/(?P<direction>up|down|clear)/$', 
        'vote_on_object', 
        {'model': OslComment, 'template_object_name': 'comment', 
        'allow_xmlhttprequest': True, 
        'template_name': 'comments/confirm_vote.html'},
        name='vote-comment'),
)


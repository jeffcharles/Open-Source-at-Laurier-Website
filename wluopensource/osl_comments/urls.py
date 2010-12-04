from django.conf.urls.defaults import *
from django.contrib.comments.urls import urlpatterns

from osl_comments.models import OslComment

urlpatterns += patterns('osl_comments.views',
    (r'^comment/(?P<comment_id>\d+)/$', 'get_comment'),
    (r'^delete_comment/(?P<comment_id>\d+)/$', 'delete_comment'),
    (r'^deleted_comment/$', 'delete_by_user_done'),
    (r'^edit/$', 'edit_comment'),
    (r'^edit_form/(?P<comment_pk>\d+)/$', 'get_ajax_edit_form'),
    (r'^edited/$', 'comment_edited'),
    (r'^flag/(?P<comment_id>\d+)/$', 'flag'),
    (r'^get_comments/(?P<obj_ctype_pk>\d+)/(?P<obj_pk>\d+)/(?P<order_method>newest|score|oldest)/(?P<comments_enabled>True|False)/$',
        'get_comments'),
    (r'^ip_address_ban/(?P<comment_id>\d+)/$', 'update_ip_address_ban'),
    (r'^ip_address_ban_update_done/$', 'update_ip_address_ban_done'),
    (r'^moderate/(?P<comment_id>\d+)/$', 'moderate'),
    url(r'^ocr/(\d+)/(.+)/$', 'redirect_view', name='osl-comments-url-redirect'),
    (r'^post2/$', 'post_comment'),
    (r'^reply_form/(?P<obj_ctype_pk>\d+)/(?P<obj_pk>\d+)/(?P<comment_pk>\d+)/$', 
        'get_ajax_reply_form')
)

VOTE_ON_OBJECT_URL_NAME = 'vote-comment'

urlpatterns += patterns('voting.views',
    url(r'^vote/(?P<object_id>\d+)/(?P<direction>up|down|clear)/$', 
        'vote_on_object', 
        {'model': OslComment, 'template_object_name': 'comment', 
        'allow_xmlhttprequest': True, 
        'template_name': 'comments/confirm_vote.html'},
        name=VOTE_ON_OBJECT_URL_NAME),
)

GET_VOTE_BOX_TEMPLATE_URL_NAME = 'get_comment_vote_box_template'

urlpatterns += patterns('osl_voting.views',
    url(r'^vote_links/(?P<object_id>\d+)/$',
    'get_vote_box_template',
    {'model': OslComment, 'vote_url_name': VOTE_ON_OBJECT_URL_NAME, 
    'vote_box_url_name': GET_VOTE_BOX_TEMPLATE_URL_NAME},
    name=GET_VOTE_BOX_TEMPLATE_URL_NAME)
)


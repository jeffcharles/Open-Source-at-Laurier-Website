from django.conf.urls.defaults import *

from osl_comments.models import OslComment

urlpatterns = patterns('django.contrib.comments.views',
    url(r'^comments/post/$',          'comments.post_comment',       name='comments-post-comment'),
    url(r'^comments/posted/$',        'comments.comment_done',       name='comments-comment-done'),
    url(r'^comments/flag/(\d+)/$',    'moderation.flag',             name='comments-flag'),
    url(r'^comments/flagged/$',       'moderation.flag_done',        name='comments-flag-done'),
    url(r'^comments/delete/(\d+)/$',  'moderation.delete',           name='comments-delete'),
    url(r'^comments/deleted/$',       'moderation.delete_done',      name='comments-delete-done'),
    url(r'^comments/approve/(\d+)/$', 'moderation.approve',          name='comments-approve'),
    url(r'^comments/approved/$',      'moderation.approve_done',     name='comments-approve-done'),
)

urlpatterns += patterns('',
    url(r'^comments/cr/(\d+)/(.+)/$', 'django.views.defaults.shortcut', name='comments-url-redirect'),
)

urlpatterns += patterns('osl_comments.views',
    (r'^comments/comment/(?P<comment_id>\d+)/$', 'get_comment'),
    (r'^comments/delete_comment/(?P<comment_id>\d+)/$', 'delete_comment'),
    (r'^comments/deleted_comment/$', 'delete_by_user_done'),
    (r'^comments/edit/$', 'edit_comment'),
    (r'^comments/edit_form/(?P<comment_pk>\d+)/$', 'get_ajax_edit_form'),
    (r'^comments/edited/$', 'comment_edited'),
    (r'^comments/get_comments/(?P<obj_ctype_pk>\d+)/(?P<obj_pk>\d+)/(?P<order_method>newest|score|oldest)/(?P<comments_enabled>True|False)/$',
        'get_comments'),
    url(r'^comments/get_comments/(?P<obj_ctype_pk>\d+)/(?P<obj_pk>\d+)/newest/(?P<comments_enabled>True|False)/$',
        'get_comments', kwargs={'order_method': 'newest'}, 
        name='get_comments_by_newest'),
    url(r'^comments/get_comments/(?P<obj_ctype_pk>\d+)/(?P<obj_pk>\d+)/score/(?P<comments_enabled>True|False)/$',
        'get_comments', kwargs={'order_method': 'score'}, 
        name='get_comments_by_score'),
    url(r'^comments/get_comments/(?P<obj_ctype_pk>\d+)/(?P<obj_pk>\d+)/oldest/(?P<comments_enabled>True|False)/$',
        'get_comments', kwargs={'order_method': 'oldest'}, 
        name='get_comments_by_oldest'),
    (r'^comments/ip_address_ban/(?P<comment_id>\d+)/$', 'update_ip_address_ban'),
    (r'^comments/ip_address_ban_update_done/$', 'update_ip_address_ban_done'),
    (r'^comments/moderate/(?P<comment_id>\d+)/$', 'moderate'),
    url(r'^comments/ocr/(\d+)/(.+)/$', 'redirect_view', name='osl-comments-url-redirect'),
    (r'^comments/post2/$', 'post_comment'),
    (r'^comments/reply_form/(?P<obj_ctype_pk>\d+)/(?P<obj_pk>\d+)/(?P<comment_pk>\d+)/$', 
        'get_ajax_reply_form')
)

VOTE_ON_OBJECT_URL_NAME = 'vote-comment'

urlpatterns += patterns('voting.views',
    url(r'^comments/vote/(?P<object_id>\d+)/(?P<direction>up|down|clear)/$', 
        'vote_on_object', 
        {'model': OslComment, 'template_object_name': 'comment', 
        'allow_xmlhttprequest': True, 
        'template_name': 'comments/confirm_vote.html'},
        name=VOTE_ON_OBJECT_URL_NAME),
)

GET_VOTE_BOX_TEMPLATE_URL_NAME = 'get_comment_vote_box_template'

urlpatterns += patterns('osl_voting.views',
    url(r'^comments/vote_links/(?P<object_id>\d+)/$',
    'get_vote_box_template',
    {'model': OslComment, 'vote_url_name': VOTE_ON_OBJECT_URL_NAME, 
    'vote_box_url_name': GET_VOTE_BOX_TEMPLATE_URL_NAME},
    name=GET_VOTE_BOX_TEMPLATE_URL_NAME)
)

urlpatterns += patterns('articles.views',
    (r'^articles/view/(?P<slug_filter>[A-Za-z0-9_-]+)/$', 'view'),
)


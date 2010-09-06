from django.conf.urls.defaults import *
from django.contrib.comments.urls import urlpatterns

urlpatterns += patterns('',
    (r'^delete_comment/(?P<comment_id>\d+)/$', 'osl_comments.views.delete_comment'),
    (r'^deleted_comment/$', 'osl_comments.views.delete_by_user_done'),
    (r'^edit/$', 'osl_comments.views.edit_comment'),
    (r'^edited/$', 'osl_comments.views.comment_edited'),
    (r'^ip_address_ban/(?P<comment_id>\d+)/$', 'osl_comments.views.update_ip_address_ban'),
    (r'^ip_address_ban_update_done/$', 'osl_comments.views.update_ip_address_ban_done'),
    url(r'^cr/(\d+)/(.+)/$', 'django.views.defaults.shortcut', name='comments-url-redirect'),
)


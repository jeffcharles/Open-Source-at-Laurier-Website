from django.conf.urls.defaults import *
from django.contrib.comments.urls import urlpatterns

urlpatterns += patterns('',
    (r'^ban_ip_address/(?P<comment_id>\d+)/$', 'osl_comments.views.ban_ip_address'),
    (r'^delete_comment/(?P<comment_id>\d+)/$', 'osl_comments.views.delete_comment'),
    (r'^deleted_comment/$', 'osl_comments.views.delete_by_user_done'),
    (r'^edit/$', 'osl_comments.views.edit_comment'),
    (r'^edited/$', 'osl_comments.views.comment_edited'),
    url(r'^cr/(\d+)/(.+)/$', 'django.views.defaults.shortcut', name='comments-url-redirect'),
)


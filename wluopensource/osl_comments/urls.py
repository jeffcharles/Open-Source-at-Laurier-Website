from django.conf.urls.defaults import *
from django.contrib.comments.urls import urlpatterns

urlpatterns += patterns('osl_comments.views',
    (r'^delete_comment/(?P<comment_id>\d+)/$', 'delete_comment'),
    (r'^deleted_comment/$', 'delete_by_user_done'),
    (r'^edit/$', 'edit_comment'),
    (r'^edited/$', 'comment_edited'),
    (r'^ip_address_ban/(?P<comment_id>\d+)/$', 'update_ip_address_ban'),
    (r'^ip_address_ban_update_done/$', 'update_ip_address_ban_done'),
    url(r'^ocr/(\d+)/(.+)/$', 'redirect_view', name='osl-comments-url-redirect'),
)


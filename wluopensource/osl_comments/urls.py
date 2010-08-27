from django.conf.urls.defaults import *
from django.contrib.comments.urls import urlpatterns

urlpatterns += patterns('',
    (r'^edit/$', 'osl_comments.views.edit_comment'),
    (r'^edited/$', 'osl_comments.views.comment_edited'),
    url(r'^cr/(\d+)/(.+)/$', 'django.views.defaults.shortcut', name='comments-url-redirect'),
)


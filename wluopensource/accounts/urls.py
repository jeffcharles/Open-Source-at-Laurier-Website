from django.conf.urls.defaults import *

urlpatterns = patterns('',
    (r'^create_account/$', 'accounts.views.create_account'),
    (r'^login/$', 'django.contrib.auth.views.login'),
    (r'^logout/$', 'django.contrib.auth.views.logout'),
    (r'^password_change/$', 'django.contrib.auth.views.password_change'),
    (r'^password_change_done/$', 'django.contrib.auth.views.password_change_done'),
    (r'^password_reset/$', 'django.contrib.auth.views.password_reset'),
    (r'^password_reset_done/$', 'django.contrib.auth.views.password_reset_done'),
    (r'^password_reset_confirm/$', 'django.contrib.auth.views.password_reset_confirm'),
    (r'^password_reset_complete/$', 'django.contrib.auth.views.password_reset_complete'),
    (r'^profile/$', 'accounts.views.profile'),
    (r'^profile_change/$', 'accounts.views.profile_change'),
)

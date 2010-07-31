from django.conf.urls.defaults import *
from django.contrib.auth.urls import urlpatterns

urlpatterns += patterns('',
    (r'^create_account/$', 'accounts.views.create_account'),
    (r'^profile/$', 'accounts.views.profile'),
    (r'^profile_change/$', 'accounts.views.profile_change'),
)

# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *

urlpatterns = patterns('articles.views',
    (r'^articles/$', 'index'),
    (r'^articles/view/$', 'blank'),
    (r'^articles/(?P<year>\d{4})/$', 'index'),
    (r'^articles/(?P<year>\d{4})/(?P<month>\d{1,2})/$', 'index'),
    (r'^articles/(?P<username>\w+)/$', 'index'),
    (r'^articles/view/(?P<slug_filter>[A-Za-z0-9_-]+)/$', 'view')
)
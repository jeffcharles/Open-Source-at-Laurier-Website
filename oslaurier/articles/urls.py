# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *

urlpatterns = patterns('oslaurier.articles.views',
    (r'^$', 'index'),
    (r'^view/$', 'blank'),
    (r'^(?P<year>\d{4})/$', 'index'),
    (r'^(?P<year>\d{4})/(?P<month>\d{1,2})/$', 'index'),
    (r'^(?P<username>\w+)/$', 'index'),
    (r'^view/(?P<slug_filter>[A-Za-z0-9_-]+)/$', 'view')
)
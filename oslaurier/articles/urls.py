# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *

urlpatterns = patterns('oslaurier.articles.views',
    (r'^$', 'index'),
    (r'^(?P<year>\d{4})/$', 'index'),
    (r'^(?P<year>\d{4})/(?P<month>\d{1,2})/$', 'index'),
    (r'^(?P<username_filter>)/$', 'index'),
    (r'^view/(?P<permalink_title_filter>)/$', 'view')
)
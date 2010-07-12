# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *

from articles.feeds import LatestArticlesRssFeed, LatestArticlesAtomFeed

urlpatterns = patterns('articles.feeds',
    (r'^rss/$', LatestArticlesRssFeed()),
    (r'^atom/$', LatestArticlesAtomFeed())
)

urlpatterns += patterns('articles.views',
    (r'^$', 'index'),
    (r'^view/$', 'blank'),
    (r'^(?P<year>\d{4})/$', 'index'),
    (r'^(?P<year>\d{4})/(?P<month>\d{1,2})/$', 'index'),
    (r'^(?P<username>\w+)/$', 'index'),
    (r'^view/(?P<slug_filter>[A-Za-z0-9_-]+)/$', 'view')
)


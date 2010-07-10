# -*- coding: utf-8 -*-
from django.conf import settings
from django.conf.urls.defaults import *
from django.contrib import admin
from django.views.generic.simple import direct_to_template

from articles.sitemap import ArticlesSitemap
from osl_flatpages.sitemap import FlatpagesSitemap

admin.autodiscover()

sitemaps = {
    'articles': ArticlesSitemap,
}

urlpatterns = patterns('',
    url(r'^$', 'osl_flatpages.views.get', {'page': 'Home'}, name="home"),
    url(r'^about/$', 'osl_flatpages.views.get', {'page': 'About'}, 
        name="about"),
    (r'^admin/doc/', include('django.contrib.admindocs.urls')),
    (r'^admin/', include(admin.site.urls)),
    (r'^announcements/', include('announcements.urls')),
    (r'^articles/', include('articles.urls')),
    url(r'^development/$', 'osl_flatpages.views.get', {'page': 'Development'},
        name="development"),
    url(r'^laurier-wireless-connect/$', 'osl_flatpages.views.get', 
        {'page': 'Laurier Wireless Connect'}, name="laurier_wireless_connect"),
    url(r'^privacy/$', 'osl_flatpages.views.get', {'page': 'Privacy'},
        name="privacy"),
        
    # used to get 'view on site' hyperlinks working in admin interface
    url(r'^r/', include('django.conf.urls.shortcut')),
    
    url('^sitemap\.xml$', 'django.contrib.sitemaps.views.sitemap',
        {'sitemaps': sitemaps}),
    url(r'^terms/$', 'osl_flatpages.views.get', {'page': 'Terms'}, 
        name="terms"),
)

if settings.DEBUG:
    urlpatterns += patterns('',
        (r'^media/(?P<path>.*)$', 'django.views.static.serve',
            {'document_root': settings.MEDIA_ROOT})
    )

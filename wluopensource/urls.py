# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *
from django.contrib import admin
from django.views.generic.simple import direct_to_template
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', 'osl_flatpages.views.get', {'page': 'Home'}, name="home"),
    url(r'^about/$', 'osl_flatpages.views.get', {'page': 'About'}, 
        name="about"),
    (r'^admin/doc/', include('django.contrib.admindocs.urls')),
    (r'^admin/', include(admin.site.urls)),
    (r'^announcements/', include('announcements.urls')),
    (r'^articles/', include('articles.urls')),
    #url(r'^development/$', direct_to_template, {'template': 'development.html'},
    #    name="development"),
    url(r'^development/$', 'osl_flatpages.views.get', {'page': 'Development'},
        name="development"),
    url(r'^privacy/$', direct_to_template, {'template': 'privacy.html'},
        name="privacy"),
    url(r'^terms/$', 'osl_flatpages.views.get', {'page': 'Terms'}, 
        name="terms"),
)

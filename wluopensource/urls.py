# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *
from django.contrib import admin
from django.views.generic.simple import direct_to_template
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', direct_to_template, {'template': 'home.html'}, name="home"),
    url(r'^about/$', direct_to_template, {'template': 'about.html'},
        name="about"),
    (r'^admin/doc/', include('django.contrib.admindocs.urls')),
    (r'^admin/', include(admin.site.urls)),
    (r'^articles/', include('articles.urls')),
    url(r'^development/$', direct_to_template, {'template': 'development.html'},
        name="development"),
    url(r'^privacy/$', direct_to_template, {'template': 'privacy.html'},
        name="privacy"),
    url(r'^terms/$', direct_to_template, {'template': 'terms.html'},
        name="terms"),
)
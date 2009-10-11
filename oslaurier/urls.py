# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *
from django.contrib import admin
from django.views.generic.simple import direct_to_template
admin.autodiscover()

urlpatterns = patterns('',
    (r'^$', direct_to_template, {
        'template': 'home.html'
    }),
    (r'^admin/doc/', include('django.contrib.admindocs.urls')),
    (r'^admin/', include(admin.site.urls)),
    (r'^articles/', include('oslaurier.articles.urls')),
)

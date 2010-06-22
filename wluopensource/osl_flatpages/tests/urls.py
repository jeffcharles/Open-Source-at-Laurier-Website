from django.conf.urls.defaults import *

urlpatterns = patterns('',
    url(r'^nonexistent/$', 'osl_flatpages.views.get', {'page': 'Nonexistent'}),
    url(r'^nontemplate/$', 'osl_flatpages.views.get', {'page': 'Nontemplate'}),
    url(r'^template/$', 'osl_flatpages.views.get', {'page': 'Template'})
)

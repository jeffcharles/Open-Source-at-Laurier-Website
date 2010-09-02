# -*- coding: utf-8 -*-
from django.contrib import admin

import settings
from articles.models import Article, ArticleForm

class ArticleAdmin(admin.ModelAdmin):
    date_hierarchy = 'date_updated'
    third_fieldset = (None, {
            'fields': ('slug',)
        })
    if "tagging" in settings.INSTALLED_APPS:
        third_fieldset = (None, {
            'fields': ('slug', 'tags')
        })    
        
    fieldsets = (
        (None, {
            'fields': ('title', 'authors', 'description', 'markdown_content')
        }),
        (None, {
            'fields': ('status', 'enable_comments',)
        }),
        third_fieldset
    )
    form = ArticleForm
    list_display = ('title', 'description', 'status', 'enable_comments', 
        'slug',)
    list_display_links = ('title',)
    list_editable = ('description', 'status', 'enable_comments',)
    list_filter = ('authors', 'status', 'enable_comments',)
    prepopulated_fields = {'slug': ('title',)}
    save_on_top = True
    search_fields = ['title', 'description']
admin.site.register(Article, ArticleAdmin)

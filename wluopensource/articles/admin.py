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
            'fields': ('draft', 'disable_comments', 'hidden')
        }),
        third_fieldset
    )
    form = ArticleForm
    list_display = ('title', 'description', 'draft', 'disable_comments', 'hidden', 'slug',)
    list_display_links = ('title',)
    list_editable = ('description', 'draft', 'disable_comments', 'hidden')
    list_filter = ('authors', 'draft', 'disable_comments', 'hidden')
    prepopulated_fields = {'slug': ('title',)}
    save_on_top = True
    search_fields = ['title', 'description']
admin.site.register(Article, ArticleAdmin)

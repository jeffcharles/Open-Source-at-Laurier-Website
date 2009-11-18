# -*- coding: utf-8 -*-
from django.contrib import admin
from articles.models import Article, ArticleForm

class ArticleAdmin(admin.ModelAdmin):
    date_hierarchy = 'date_updated'
    fieldsets = (
        (None, {
            'fields': ('title', 'authors', 'description', 'markdown_content')
        }),
        (None, {
            'fields': ('draft', 'disable_comments', 'hidden')
        }),
        (None, {
            'fields': ('slug',)
        })
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
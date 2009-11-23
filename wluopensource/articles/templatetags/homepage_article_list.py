# -*- coding: utf-8 -*-
from django import template
from articles.models import Article

register = template.Library()

@register.inclusion_tag('articles/homepage_list_articles.html')
def list_articles(number_to_return):
    articles = (Article.objects.exclude(draft=True).exclude(hidden=True)
        .order_by('-date_created')[:number_to_return])
    return {'articles': articles}
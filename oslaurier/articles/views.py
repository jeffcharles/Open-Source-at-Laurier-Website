# -*- coding: utf-8 -*-
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404
from oslaurier.articles.models import Article
from oslaurier.jinja2integration.djangojinja2 import render_to_response

def __get_articles(article_list):
    """
    Returns a list of articles based on page given and number of articles to
    display

    Parameters:
        article_list - a list of articles from the database
    """
    paginator = Paginator(article_list, __get_number_per_page(request))
    page = __get_page()
    try:
        articles = paginator.page(page)
    except (EmptyPage, InvalidPage):
        articles = paginator.page(paginator.num_pages)
    return articles

def __get_order_by_title(request):
    """
    Returns whether to order the articles by title or by most recent
    """
    try:
        order_by_title = int(request.GET.get('order_by_title', 0))
    except:
        order_by_title = 0
    return order_by_title

def __get_page():
    """
    Returns the page number in the paginated list present in the query string
    """
    try:
        page = int(request.GET.get('page', 1))
    except:
        page = 1
    return page

def __get_number_per_page(request):
    """
    Returns the number of articles to display on a page
    """
    try:
        num_per_page = int(request.GET.get('num_per_page', 10))
    except:
        num_per_page = 10
    return num_per_page

def index(request, month_filter=None, username_filter=None, year_filter=None):
    """
    Render a response with a list of articles
    """
    order_by_title = __get_order_by_title
    if order_by_title:
        order = 'title'
    else:
        order = '-date_created'

    if month_filter not None and year_filter not None:
        article_list =
            Article.objects.get(month=month_filter,
            year=year_filter).order_by(order)
    elif year_filter not None:
        article_list = Article.objects.get(year=year_filter).order_by(order)
    elif username_filter not None:
        article_list = \
            Article.objects.get(username=username_filter).order_by(order)
    else:
        article_list = Article.objects.all().order_by(order)

    articles = __get_articles(article_list)
    return render_to_response('list.html', {'articles': articles})

def view(request, title_filter):
    """
    Render a response with the specified articles
    """
    article = get_object_or_404(Article, permalink_title=permalink_title_filter)
    return render_to_response('view.html', {'article': article})
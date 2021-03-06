# -*- coding: utf-8 -*-
from datetime import date
from django.core.paginator import EmptyPage, InvalidPage, Paginator
from django.http import Http404
from django.http import HttpResponseForbidden, HttpResponseServerError
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext
from articles.models import Article

def __get_articles(request, article_list, number_per_page):
    """
    Returns a list of articles based on page given and number of articles to
    display

    Parameters:
        request         - the http request
        article_list    - a list of articles from the database
        number_per_page - the number of articles to display on a page
    """
    paginator = Paginator(article_list, __get_number_per_page(request))
    page = __get_page(request)
    try:
        articles = paginator.page(page)
    except (EmptyPage, InvalidPage):
        articles = None
    return articles

def __get_order_by_title(request):
    """
    Returns whether to order the articles by title or by most recent
    """
    try:
        order_by_title = int(request.GET.get('order_by_title', 0))
    except:
        order_by_title = 0
    order_by_title = bool(order_by_title)
    return order_by_title

def __get_page(request):
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

def blank(request):
    """
    If user requests an article without supplying a slug, then throw a 404 error
    """
    raise Http404()

def index(request, month=None, username=None, year=None):
    """
    Render a response with a list of articles
    """
    order_by_title = __get_order_by_title(request)
    if order_by_title:
        order = 'title'
    else:
        order = '-date_created'

    article_list = \
        Article.objects.filter(status=Article.LIVE_STATUS).order_by(order)

    if month is not None and year is not None:
        article_list = (article_list.filter(date_created__year=year)
            .filter(date_created__month=month))
    elif year is not None:
        article_list = \
            article_list.filter(date_created__year=year)
    elif username is not None:
        article_list = \
            article_list.filter(authors__username=username)

    number_per_page = __get_number_per_page(request)
    articles = __get_articles(request, article_list, number_per_page)
    return render_to_response('articles/list.html',
        {'articles': articles, 'num_per_page': number_per_page},
        context_instance=RequestContext(request))

def view(request, slug_filter):
    """
    Render a response with the specified articles
    """
    article = get_object_or_404(Article, slug=slug_filter)

    # if article is hidden return 403 error
    if article.status == Article.HIDDEN_STATUS:
        return HttpResponseForbidden("<h1>You are not authorized to view this \
            page</h1>")

    return render_to_response('articles/view.html',
        {'article': article},
        context_instance=RequestContext(request))

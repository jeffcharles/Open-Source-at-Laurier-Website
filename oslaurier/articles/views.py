# -*- coding: utf-8 -*-
from datetime import date
from django.core.paginator import EmptyPage, InvalidPage, Paginator
from django.http import Http404
from django.http import HttpResponseForbidden, HttpResponseServerError
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext
from oslaurier.articles.models import Article

def __get_articles(request, article_list):
    """
    Returns a list of articles based on page given and number of articles to
    display

    Parameters:
        request      - the http request
        article_list - a list of articles from the database
    """
    paginator = Paginator(article_list, __get_number_per_page(request))
    page = __get_page(request)
    try:
        articles = paginator.page(page)
    except (EmptyPage, InvalidPage):
        articles = paginator.page(paginator.num_pages)
    return articles

def __get_authors(article):
    """
    Returns a string containing all of the articles authors
    """
    number_of_authors = len(article.authors.all())
    if number_of_authors == 1:
        authors = article.authors.all()[0].get_full_name()
    elif number_of_authors == 2:
        authors = " and ".join([author.get_full_name()
            for author in article.authors.all()])
    elif number_of_authors > 2:
        authors = ", and ".join(
            [", ".join([author.get_full_name()
            for author in article.authors.all()[1:]]),
            article.authors.all()[0].get_full_name()])
    else:
        return HttpResponseServerError("<h1>A server error has occurred</h1> \
            <p>Please contact the webmaster with the url you attempted to \
            access.</p>")
    return authors

def __get_order_by_title(request):
    """
    Returns whether to order the articles by title or by most recent
    """
    try:
        order_by_title = int(request.GET.get('order_by_title', 0))
    except:
        order_by_title = 0
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
    order_by_title = __get_order_by_title
    if order_by_title:
        order = 'title'
    else:
        order = '-date_created'

    article_list = \
        Article.objects.exclude(draft=True).exclude(hidden=True).order_by(order)

    if month is not None and year is not None:
        article_list = (article_list.filter(date_created__year=year)
            .filter(date_created__month=month))
    elif year is not None:
        article_list = \
            article_list.filter(date_created__year=year)
    elif username is not None:
        article_list = \
            article_list.filter(authors__username=username)

    articles = __get_articles(request, article_list)
    return render_to_response('articles/list.html', {'articles': articles},
        context_instance=RequestContext(request))

def view(request, slug_filter):
    """
    Render a response with the specified articles
    """
    article = get_object_or_404(Article, slug=slug_filter)

    # if article is hidden or a draft, return 403 error
    if article.hidden or article.draft:
        return HttpResponseForbidden("<h1>You are not authorized to view this \
            page</h1>")

    authors = __get_authors(article)
    return render_to_response('articles/view.html',
        {'article': article, 'authors': authors},
        context_instance=RequestContext(request))
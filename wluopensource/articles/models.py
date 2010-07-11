# -*- coding: utf-8 -*-
from datetime import datetime

from django.contrib.auth.models import User
from django.contrib.sitemaps import ping_google, SitemapNotFound
from django.db import models
from django.db.models.signals import post_init
from django.forms import ModelForm

import markdown

import settings
if "tagging" in settings.INSTALLED_APPS:
    from tagging.fields import TagField

class Article(models.Model):
    LIVE_STATUS = 0
    DRAFT_STATUS = 1
    HIDDEN_STATUS = 2
    STATUS_CHOICES = (
        (LIVE_STATUS, 'Live'),
        (DRAFT_STATUS, 'Draft'),
        (HIDDEN_STATUS, 'Hidden'),
    )
    
    __orig_status = None

    title = models.CharField(max_length=100, unique=True)
    authors = models.ManyToManyField(User)
    date_created = models.DateField('date created', auto_now_add=True)
    date_updated = models.DateField('date updated', auto_now=True)
    description = models.CharField(max_length=200)
    markdown_content = models.TextField('content')
    content = models.TextField(editable=False)
    status = models.IntegerField(choices=STATUS_CHOICES, default=LIVE_STATUS,
        db_index=True)
    disable_comments = models.BooleanField('disable comments?', default=False)
    slug = models.SlugField(max_length=50)
    if "tagging" in settings.INSTALLED_APPS:
        tags = TagField()

    def __init__(self, *args, **kwargs):
        super(Article, self).__init__(*args, **kwargs)
        self.__orig_status = self.status

    def __unicode__(self):
        return self.title

    def __adjust_date_created(self):
        """
        Reset date created if article is changing from draft to something else
        
        Only called from save method.
        
        Going from draft to draft should not change anything:
        >>> from datetime import timedelta
        >>> a = Article()
        >>> a.title = "Adjust date created"
        >>> a.status = Article.DRAFT_STATUS
        >>> a.save()
        >>> a.date_created -= timedelta(days=1)
        >>> a.save()
        >>> orig_date = a.date_created.date()
        >>> a = None
        >>> a = Article.objects.get(title="Adjust date created")
        >>> a.status = Article.DRAFT_STATUS
        >>> a.save()
        >>> a.date_created == orig_date
        True
        
        Going from draft to live should change the date created:
        >>> a = Article()
        >>> a.title = "Adjust date created 2"
        >>> a.status = Article.DRAFT_STATUS
        >>> a.save()
        >>> a.date_created -= timedelta(days=1)
        >>> a.save()
        >>> orig_date = a.date_created.date()
        >>> a = None
        >>> a = Article.objects.get(title="Adjust date created 2")
        >>> a.status = Article.LIVE_STATUS
        >>> a.save()
        >>> a.date_created.date() > orig_date
        True
        
        Going from live to draft should not change the date created:
        >>> a = Article()
        >>> a.title = "Adjust date created 3"
        >>> a.status = Article.LIVE_STATUS
        >>> a.save()
        >>> a.date_created -= timedelta(days=1)
        >>> a.save()
        >>> orig_date = a.date_created.date()
        >>> a = None
        >>> a = Article.objects.get(title="Adjust date created")
        >>> a.status = Article.DRAFT_STATUS
        >>> a.save()
        >>> a.date_created == orig_date
        True
        """
        if self.__orig_status == self.DRAFT_STATUS and \
                self.status != self.DRAFT_STATUS:
            self.date_created = datetime.now()

    def __convert_markdown_content_to_html(self):
        """
        Transform markdown content into html content
        
        >>> a = Article()
        >>> a.title = "Markdown content to html"
        >>> a.markdown_content = "# Something! #"
        >>> a.save()
        >>> a.content
        u'<h1>Something!</h1>'
        """
        self.content = markdown.markdown(self.markdown_content)
    
    def __ping_google(self):
        """
        Pings Google to let them know sitemap has been updated
        """
        try:
            ping_google()
        except SitemapNotFound:
            raise
        except Exception:
            # Could get variety of HTTP-related exceptions, pinging Google is
            # not critical so just swallow exception
            pass

    @models.permalink
    def get_absolute_url(self):
        return ('articles.views.view', (), {'slug_filter': self.slug})

    def save(self, force_insert=False, force_update=False):
        """
        Transform Markdown content into HTML content and update date created
        if article is going from draft to live status
        """
        self.__convert_markdown_content_to_html()
        self.__adjust_date_created()
        if not self.id:
            insert = True
        else:
            insert = False
        super(Article, self).save(force_insert, force_update)
        if insert:
            self.__ping_google()

class ArticleForm(ModelForm):
    class Meta:
        model = Article

    def clean_permalink_title(self):
        permalink_title = self.cleaned_data['permalink_title']
        if re.search("[^A-Za-z0-9 -]", permalink_title) is not None:
            raise forms.ValidationError("Permalink titles can only contain "
                "alphanumeric characters and spaces or dashes")
        permalink_title = permalink_title.replace(" ", "-")
        return permalink_title

# -*- coding: utf-8 -*-
import markdown

from django.db import models
from django.contrib.auth.models import User
from django.forms import ModelForm

import settings
if "tagging" in settings.INSTALLED_APPS:
    from tagging.fields import TagField

class Article(models.Model):
    title = models.CharField(max_length=100, unique=True)
    authors = models.ManyToManyField(User)
    date_created = models.DateField('date created', auto_now_add=True)
    date_updated = models.DateField('date updated', auto_now=True)
    description = models.CharField(max_length=200)
    markdown_content = models.TextField('content')
    content = models.TextField(editable=False)
    draft = models.BooleanField('draft?', default=False)
    disable_comments = models.BooleanField('disable comments?', default=False)
    hidden = models.BooleanField('hide?', default=False)
    slug = models.SlugField(max_length=50)
    if "tagging" in settings.INSTALLED_APPS:
        tags = TagField()

    def __unicode__(self):
        return self.title

    def get_absolute_url(self):
        return "/articles/view/%s/" % self.slug

    def save(self, force_insert=False, force_update=False):
        self.content = markdown.markdown(self.markdown_content)
        super(Article, self).save(force_insert, force_update)
        
    def _get_authors(self):
        """
        Returns a string containing all of the articles' authors
        """
        number_of_authors = len(self.authors.all())
        if number_of_authors == 1:
            authors = self.authors.order_by('last_name')[0].get_full_name()
        elif number_of_authors == 2:
            authors = " and ".join([author.get_full_name()
                for author in self.authors.order_by('last_name')])
        elif number_of_authors > 2:
            authors = ", and ".join(
                [", ".join([author.get_full_name() for author in 
                self.authors.order_by('last_name')[:number_of_authors-1]]),
                self.authors.order_by('last_name')[number_of_authors-1].get_full_name()])
        else:
            return HttpResponseServerError("<h1>A server error has occurred</h1> \
                <p>Please contact the webmaster with the url you attempted to \
                access.</p>")
        return authors
    author_string = property(_get_authors)

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

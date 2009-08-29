# -*- coding: utf-8 -*-
from django.db import models
from django.contrib.auth.models import User

class Article(models.Model):
    title = models.CharField(max_length=100, unique=True)
    authors = ManyToManyField(User)
    date_created = models.DateField('date created', auto_now_add=True)
    date_updated = models.DateField('date updated', auto_now=True)
    slug = models.SlugField()
    content = models.TextField()
    disable_comments = models.BooleanField('disable comments?', default=False)

    def __unicode__(self):
        return self.title

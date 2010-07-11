import markdown

from django.db import models
from django.forms import ModelForm

import settings

class Flatpage(models.Model):
    """
    Custom flatpage model.
    
    This is different from the default flatpage model because it uses Markdown 
    in the content to convert up to HTML. It also allows for template tags to
    be used in content.
    
    Pages are retrieved via specifying the page name in a named url in the 
    urlconf.
    
    Doctests for get_absolute_url have been moved up here because they don't 
    work when placed in the get_absolute_url docstring.
    
    Test that homepage works:
    >>> home_fp = Flatpage.objects.get(page_name="Home")
    >>> home_fp.get_absolute_url()
    '/'
    
    Test that about page works:
    >>> about_fp = Flatpage.objects.get(page_name="About")
    >>> about_fp.get_absolute_url()
    '/about/'    
    """
    page_name = models.CharField(max_length=100, primary_key=True, unique=True)
    title = models.CharField(blank=True, max_length=100)
    description = models.CharField(blank=True, max_length=255)
    markdown_content = models.TextField('content')
    content = models.TextField(editable=False)
    
    class Meta:
        ordering = ['page_name']
    
    def __unicode__(self):
        return self.page_name
    
    def get_absolute_url(self):
        """
        Use urlconf to determine url name from page name and then use url name
        to get absolute url. 
        
        Returns none if there is no url name associated with the page name.
        """
        from django.core.urlresolvers import reverse
        from urls import urlpatterns
        
        for urlpattern in urlpatterns:
            if (hasattr(urlpattern, "default_args") and
                "page" in urlpattern.default_args and
                urlpattern.default_args["page"] == self.page_name and
                hasattr(urlpattern, "name")):
                
                return reverse(urlpattern.name)
                
        return None
        
    def save(self, force_insert=False, force_update=False):
        self.content = markdown.markdown(self.markdown_content)
        super(Flatpage, self).save(force_insert, force_update)


import markdown

from django.db import models

import settings

class Flatpage(models.Model):
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
        Search for page name in urlconf, raise an exception if not found
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
    

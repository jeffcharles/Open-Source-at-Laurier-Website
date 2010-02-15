from django.db import models
import markdown

class Flatpage(models.Model):
    page_name = models.CharField(max_length=100, primary_key=True, unique=True)
    title = models.CharField(blank=True, max_length=100)
    description = models.CharField(blank=True, max_length=255)
    markdown_content = models.TextField('content')
    content = models.TextField(editable=False)
    
    def __unicode__(self):
        return self.page_name
        
    def save(self, force_insert=False, force_update=False):
        self.content = markdown.markdown(self.markdown_content)
        super(Flatpage, self).save(force_insert, force_update)
    

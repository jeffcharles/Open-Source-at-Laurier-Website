from django.db import models
import markdown

class Flatpage(models.Model):
    page_name = models.CharField(max_length=100, primary_key=True, unique=True)
    markdown_content = models.TextField('content')
    content = models.TextField(editable=False)
    
    def __unicode__(self):
        return self.page_name
        
    def save(self, force_insert=False, force_update=False):
        self.content = markdown.markdown(self.markdown_content)
        super(Flatpage, self).save(force_insert, force_update)
    

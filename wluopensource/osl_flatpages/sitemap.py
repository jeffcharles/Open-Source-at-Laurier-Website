from datetime import datetime, time

from django.contrib.sitemaps import Sitemap

from osl_flatpages.models import Flatpage

class FlatpagesSitemap(Sitemap):
    changefreq = "never"
    
    def items(self):
        return Flatpage.objects.all()
        

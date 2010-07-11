from django.contrib.sitemaps import Sitemap

from osl_flatpages.models import Flatpage

class FlatpagesSitemap(Sitemap):
    
    def changefreq(self, obj):
        return obj.changefreq
    
    def items(self):
        return Flatpage.objects.all()
        

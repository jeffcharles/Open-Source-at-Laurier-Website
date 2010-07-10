from datetime import datetime, time

from django.contrib.sitemaps import Sitemap

from articles.models import Article

class ArticlesSitemap(Sitemap):
    changefreq = "never"
    
    def items(self):
        return Article.objects.filter(status=Article.LIVE_STATUS)
        
    def lastmod(self, obj):
        return datetime.combine(obj.date_updated, time())

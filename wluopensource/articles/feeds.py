from django.contrib.syndication.views import Feed
from django.utils.feedgenerator import Atom1Feed

from articles.models import Article

class LatestArticlesRssFeed(Feed):
    title = "Open Source at Laurier articles"
    link = "/articles/"
    description = "Various articles revolving around open source software and \
Open Source at Laurier"
    
    def items(self):
        return Article.objects.filter(status=Article.LIVE_STATUS).order_by('-date_created')[:5]
        
    def item_description(self, item):
        return item.description
        
    def item_title(self, item):
        return item.title
        
class LatestArticlesAtomFeed(LatestArticlesRssFeed):
    feed_type = Atom1Feed
    subtitle = LatestArticlesRssFeed.description
        

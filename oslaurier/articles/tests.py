# -*- coding: utf-8 -*-
from django.test import TestCase
from django.test.client import Client
from oslaurier.articles.models import Article

class ArticleTestCase(TestCase):
    # fixture data:
    #   Users:
    #       jeff
    #       siraj
    #       blake
    #   Articles:
    #       Hello World (hello-world), least recent
    #       A draft article (draft-article)
    #       A hidden article (hidden-article)
    #       Two author article (two-author-article)
    #       Multi-author article (multi-author-article), most recent
    fixtures = ['test_fixture.json']
    urls = 'articles.test_urls'

    def setUp(self):
        self.client = Client()

    def test_index(self):
        """
        Test that article index page returns a 200 response
        """
        response = self.client.get('/articles/')
        self.failUnlessEqual(response.status_code, 200)

    def test_index_default_list(self):
        """
        Test that index is only displaying non-draft, non-hidden articles
        """
        response = self.client.get('/articles/')
        hello_world = Article.objects.get(slug='hello-world')
        two_author = Article.objects.get(slug='two-author-article')
        multi_author = Article.objects.get(slug='multi-author-article')
        self.assertEqual(list(response.context['articles'].object_list).sort(),
            [multi_author, two_author, hello_world].sort())

    def test_index_recent_list_order(self):
        """
        Test that index is displaying articles in most recent order_by_title
        """
        response = self.client.get('/articles/')
        hello_world = Article.objects.get(slug='hello-world')
        two_author = Article.objects.get(slug='two-author-article')
        multi_author = Article.objects.get(slug='multi-author-article')
        self.assertEqual(list(response.context['articles'].object_list),
            [multi_author, two_author, hello_world])

    def test_index_empty_month_list(self):
        """
        Test that index displays no articles in a month where there isn't any
        """
        response = self.client.get('/articles/2009/07/')
        self.assertTrue(len(response.context['articles'].object_list) == 0)

    def test_index_empty_username_list(self):
        """
        Test that index displays no articles for a username without one
        """
        response = self.client.get('/articles/aaaaaaaaaa/')
        self.assertTrue(len(response.context['articles'].object_list) == 0)

    def test_index_empty_year_list(self):
        """
        Test that index displays no articles in a year where there isn't any
        """
        response = self.client.get('/articles/2008/')
        self.assertTrue(len(response.context['articles'].object_list) == 0)

    def test_index_has_no_next_anchors(self):
        """
        Test that index has no next anchor for this fixture
        """
        response = self.client.get('/articles/')
        self.assertEqual(response.content.find(
            '<a href="/articles/?num_per_page=10&page=2">Next</a>'), -1)

    def test_index_has_no_other_pages(self):
        """
        Test that index has no other pages for this fixture
        """
        response = self.client.get('/articles/')
        self.assertFalse(response.context['articles'].has_other_pages())

    def test_index_has_no_prev_anchors(self):
        """
        Test that index has no previous anchor for this fixture
        """
        response = self.client.get('/articles/')
        self.assertEqual(response.content.find(
            '<a href="/articles/?page=0">Next</a>'), -1)

    def test_index_month_list(self):
        """
        Test that index displays at least one article in a month where there
        should be one
        """
        response = self.client.get('/articles/2009/10/')
        self.assertTrue(len(response.context['articles'].object_list) > 0)

    def test_index_order_by_title(self):
        """
        Test that index displays articles in order of title when prompted
        """
        response = self.client.get('/articles/?order_by_title=1')
        hello_world = Article.objects.get(slug='hello-world')
        two_authors = Article.objects.get(slug='two-author-article')
        multi_authors = Article.objects.get(slug='multi-author-article')
        self.assertEqual(list(response.context['articles'].object_list),
            [hello_world, multi_authors, two_authors])

    def test_index_template(self):
        """
        Test that index uses the correct template
        """
        response = self.client.get('/articles/')
        self.assertEqual(response.template[0].name, 'articles/list.html')

    def test_index_username(self):
        """
        Test that index displays at least one article for a username that has
        at least one
        """
        response = self.client.get('/articles/jeff/')
        self.assertTrue(len(response.context['articles'].object_list) > 0)

    def test_index_year_list(self):
        """
        Test that index displays at least one article in a year where there
        should be one
        """
        response = self.client.get('/articles/2009/')
        self.assertTrue(len(response.context['articles'].object_list) > 0)

    def test_view_blank(self):
        """
        Test that article view without a slug returns a 404 response
        """
        response = self.client.get('/articles/view/')
        self.failUnlessEqual(response.status_code, 404)

    def test_view_draft(self):
        """
        Test that draft article view returns a 403 response
        """
        response = self.client.get('/articles/view/draft-article/')
        self.failUnlessEqual(response.status_code, 403)

    def test_view_hidden(self):
        """
        Test that hidden article view returns a 403 response
        """
        response = self.client.get('/articles/view/hidden-article/')
        self.failUnlessEqual(response.status_code, 403)

    def test_view_invalid(self):
        """
        Test that invalid article view page returns a 404 response
        """
        response = self.client.get('/articles/view/aaaaaaaaaaaa/')
        self.failUnlessEqual(response.status_code, 404)

    def test_view_multi_authors(self):
        """
        Test that multi-author article view page returns a 200 response
        """
        response = self.client.get('/articles/view/multi-author-article/')
        self.failUnlessEqual(response.status_code, 200)

    def test_view_multi_authors_formatting(self):
        """
        Test that articles with multiple authors have the authors' names
        outputted correctly
        """
        response = self.client.get('/articles/view/multi-author-article/')
        self.assertEqual(response.context['authors'],
            u'Siraj Mithoowani, Blake Vollbrecht, and Jeffrey Charles')

    def test_view_single_author_formatting(self):
        """
        Test that article with single author has author name outputted correctly
        """
        response = self.client.get('/articles/view/hello-world/')
        self.assertEqual(response.context['authors'], u'Jeffrey Charles')

    def test_view_template(self):
        """
        Test that article view loads the correct template
        """
        response = self.client.get('/articles/view/hello-world/')
        self.assertEqual(response.template[0].name, 'articles/view.html')

    def test_view_two_authors(self):
        """
        Test that two author article view page returns a 200 response
        """
        response = self.client.get('/articles/view/two-author-article/')
        self.failUnlessEqual(response.status_code, 200)

    def test_view_two_authors_formatting(self):
        """
        Test that article with two authors has author names outputted correctly
        """
        response = self.client.get('/articles/view/two-author-article/')
        self.assertEqual(response.context['authors'],
            u'Jeffrey Charles and Siraj Mithoowani')

    def test_view_valid(self):
        """
        Test that valid article view page returns a 200 response
        """
        response = self.client.get('/articles/view/hello-world/')
        self.failUnlessEqual(response.status_code, 200)

class ArticlePaginationTestCase(TestCase):
    fixtures = ['pagination.json']
    urls = 'articles.test_urls'

    def setUp(self):
        self.client = Client()
        self.article1 = Article.objects.get(slug='hello-world')
        self.article2 = Article.objects.get(slug='two-author-article')
        self.article3 = Article.objects.get(slug='multi-author-article')
        self.article4 = Article.objects.get(slug='article-4')
        self.article5 = Article.objects.get(slug='article-5')
        self.article6 = Article.objects.get(slug='article-6')
        self.article7 = Article.objects.get(slug='article-7')
        self.article8 = Article.objects.get(slug='article-8')
        self.article9 = Article.objects.get(slug='article-9')
        self.article10 = Article.objects.get(slug='article-10')
        self.article11 = Article.objects.get(slug='article-11')
        self.article12 = Article.objects.get(slug='article-12')
        self.article13 = Article.objects.get(slug='article-13')
        self.article14 = Article.objects.get(slug='article-14')
        self.article15 = Article.objects.get(slug='article-15')
        self.article16 = Article.objects.get(slug='article-16')
        self.article17 = Article.objects.get(slug='article-17')
        self.article18 = Article.objects.get(slug='article-18')
        self.article19 = Article.objects.get(slug='article-19')
        self.article20 = Article.objects.get(slug='article-20')
        self.article21 = Article.objects.get(slug='article-21')

    def test_default_num_per_page(self):
        """
        Test that the default number of articles per page is 10
        """
        response = self.client.get('/articles/')
        self.assertEqual(len(response.context['articles'].object_list), 10)

    def test_first_set_has_next(self):
        """
        Test that first set of articles has a next set
        """
        response = self.client.get('/articles/?num_per_page=10')
        self.assertTrue(response.context['articles'].has_next())

    def test_first_set_has_next_anchor(self):
        """
        Test that an appropriate anchor is outputted for going to the next set
        """
        response = self.client.get('/articles/?num_per_page=10')
        self.assertNotEqual(response.content.find(
            '<a href="/articles/?page=2>Next</a>'), -1)

    def test_first_set_not_has_previous(self):
        """
        Test that first set of articles does not have a previous set
        """
        response = self.client.get('/articles/?num_per_page=10')
        self.assertFalse(response.context['articles'].has_previous())

    def test_first_set_not_has_previous_anchor(self):
        """
        Test that first set of articles does not have an anchor to a previous
        set
        """
        response = self.client.get('/articles/?num_per_page=10')
        self.assertEqual(response.content.find(
            '<a href="/articles/?page=0>Previous</a>'), -1)

    def test_invalid_page(self):
        """
        Test that first set of articles is returned if invalid page is given
        """
        response = self.client.get('/articles/?page=a')
        self.assertEqual(response.context['articles'].number, 1)

    def test_invalid_per_page_setting(self):
        """
        Test that giving an invalid per page setting results in the default
        number of articles per page being used
        """
        response = self.client.get('/articles/?num_per_page=a')
        self.assertEqual(len(response.context['articles'].object_list), 10)

    def test_page_beyond_end(self):
        """
        Test that a 404 is returned if a page beyond the number of articles is
        requested
        """
        response = self.client.get('/articles/?num_per_page=10&page=4')
        self.assertEqual(response.status_code, 404)

    def test_second_set_has_next(self):
        """
        Test that second set of articles has a next set
        """
        response = self.client.get('/articles/?num_per_page=10&page=2')
        self.assertTrue(response.context['articles'].has_next())

    def test_second_set_has_next_anchor(self):
        """
        Test that second set of articles has an anchor to the next set
        """
        response = self.client.get('/articles/?num_per_page=10&page=2')
        self.assertNotEqual(response.content.find(
            '<a href="/articles/?page=3>Next</a>'), -1)

    def test_second_set_has_previous(self):
        """
        Test that second set of articles has previous set
        """
        response = self.client.get('/articles/?num_per_page=10&page=2')
        self.assertTrue(response.context['articles'].has_previous())

    def test_second_set_has_previous_anchor(self):
        """
        Test that second set of articles has anchor to previous set
        """
        response = self.client.get('/articles/?num_per_page=10&page=2')
        self.assertNotEqual(response.content.find(
            '<a href="/articles/?page=1>Previous</a>'), -1)

    def test_third_set_not_has_next(self):
        """
        Test that third set of articles does not have a next set
        """
        response = self.client.get('/articles/?num_per_page=10&page=3')
        self.assertFalse(response.context['articles'].has_next())

    def test_third_set_not_has_next_anchor(self):
        """
        Test that third set of articles does not have a next anchor
        """
        response = self.client.get('/articles/?num_per_page=10&page=3')
        self.assertEqual(response.content.find(
            '<a href="/articles/?num_per_page=10&page=4">Next</a>'), -1)

    def test_third_set_has_previous(self):
        """
        Test that third set of articles does have a previous set
        """
        response = self.client.get('/articles/?num_per_page=10&page=3')
        self.assertTrue(response.context['articles'].has_previous())

    def test_third_set_has_previous_anchor(self):
        """
        Test that third set of articles does have a previous set
        """
        response = self.client.get('/artcles/?num_per_page=10&page=3')
        self.assertNotEqual(response.content.find(
            '<a href="/articles/?num_per_page=10&page=2">Previous</a>'), -1)

    def test_valid_per_page_setting(self):
        """
        Test that per page value is correct given a different number of
        articles to display than the default number
        """
        response = self.client.get('/articles/?num_per_page=15')
        self.assertEqual(len(response.context['articles'].object_list), 15)

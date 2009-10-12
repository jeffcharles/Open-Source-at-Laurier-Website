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

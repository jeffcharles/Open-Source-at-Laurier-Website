import os

from django.conf import settings
from django.test import TestCase
from django.test.client import Client

from osl_comments.models import CommentsBannedFromIpAddress

class CommentsTestCase(TestCase):
    fixtures = ['comments_test_data.json']
    urls = 'osl_comments.tests.urls'
    
    def setUp(self):
        self.old_LANGUAGES = settings.LANGUAGES
        self.old_LANGUAGE_CODE = settings.LANGUAGE_CODE
        settings.LANGUAGES = (('en', 'English'),)
        settings.LANGUAGE_CODE = 'en'
        self.old_TEMPLATE_DIRS = settings.TEMPLATE_DIRS
        settings.TEMPLATE_DIRS = (
            os.path.join(
                os.path.dirname(__file__),
                'templates'
            )
        ,)
    
    def tearDown(self):
        settings.LANGUAGES = self.old_LANGUAGES
        settings.LANGUAGE_CODE = self.old_LANGUAGE_CODE
        settings.TEMPLATE_DIRS = self.old_TEMPLATE_DIRS
    
    def testAnonFewCommentsArticleAccess(self):
        response = self.client.get('/articles/view/few-comments/')
        self.assertEquals(response.status_code, 200)
    
    def testAnonLotsOfCommentsArticleAccess(self):
        response = self.client.get('/articles/view/lots-comments/')
        self.assertEquals(response.status_code, 200)
    
    def testAnonNoCommentsArticleAccess(self):
        response = self.client.get('/articles/view/no-comments/')
        self.assertEquals(response.status_code, 200)
    
    def testAuthFewCommentsArticleAccess(self):
        self.client.login(username='auth_user', password='password')
        response = self.client.get('/articles/view/few-comments/')
        self.assertEquals(response.status_code, 200)
        
    def testAuthLotsOfCommentsArticleAccess(self):
        self.client.login(username='auth_user', password='password')
        response = self.client.get('/articles/view/lots-comments/')
        self.assertEquals(response.status_code, 200)        
        
    def testAuthNoCommentsArticleAccess(self):
        self.client.login(username='auth_user', password='password')
        response = self.client.get('/articles/view/no-comments/')
        self.assertEquals(response.status_code, 200)
        
    def testSuperUserFewCommentsArticleAccess(self):
        self.client.login(username='jeff', password='password')
        response = self.client.get('/articles/view/few-comments/')
        self.assertEquals(response.status_code, 200)
        
    def testSuperUserLotsOfCommentsArticleAccess(self):
        self.client.login(username='jeff', password='password')
        response = self.client.get('/articles/view/lots-comments/')
        self.assertEquals(response.status_code, 200)
        
    def testSuperUserNoCommentsArticleAccess(self):
        self.client.login(username='jeff', password='password')
        response = self.client.get('/articles/view/no-comments/')
        self.assertEquals(response.status_code, 200)
    
    def testBannedFromCommentingLotsOfCommentsArticleAccess(self):
        ban = CommentsBannedFromIpAddress(ip_address='127.0.0.1')
        ban.save()
        response = self.client.get('/articles/view/lots-comments/')
        self.assertEquals(response.status_code, 200)
    
    def testBannedFromCommentingNoCommentsArticleAccess(self):
        ban = CommentsBannedFromIpAddress(ip_address='127.0.0.1')
        ban.save()
        response = self.client.get('/articles/view/no-comments/')
        self.assertEquals(response.status_code, 200)


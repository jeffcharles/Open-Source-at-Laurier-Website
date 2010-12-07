import os

from django.conf import settings
from django.test import TestCase
from django.test.client import Client

from articles.models import Article
from osl_comments.models import CommentsBannedFromIpAddress, OslComment

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
        
    ## Article access tests ##
    
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
    
    ## Delete comment tests ##
    
    def testNominalDeleteCommentStatus(self):
        self.client.login(username='jeff', password='password')
        response = self.client.post('/comments/delete_comment/1/')
        self.assertEquals(response.status_code, 302)
    
    def testNominalDeleteCommentLocation(self):
        self.client.login(username='jeff', password='password')
        response = self.client.post('/comments/delete_comment/1/')
        self.assertEquals(response['location'], 
            'http://testserver/comments/deleted_comment/?c=1')
    
    def testCommentNotDeletedByDefault(self):
        oc = OslComment.objects.get(pk=1)
        self.assertEquals(oc.is_deleted_by_user, False)
    
    def testNominalDeleteCommentResult(self):
        self.client.login(username='jeff', password='password')
        self.client.post('/comments/delete_comment/1/')
        oc = OslComment.objects.get(pk=1)
        self.assertEquals(oc.is_deleted_by_user, True)
    
    def testDeleteCommentAuthRequiredStatus(self):
        response = self.client.post('/comments/delete_comment/1/')
        self.assertEquals(response.status_code, 302)
        
    def testDeleteCommentAuthRequiredLocation(self):
        response = self.client.post('/comments/delete_comment/1/')
        self.assertEquals(response['location'], 
            'http://testserver/accounts/login/?next=/comments/delete_comment/1/')
    
    def testDeleteCommentAuthRequiredResult(self):
        self.client.post('/comments/delete_comment/1/')
        oc = OslComment.objects.get(pk=1)
        self.assertEquals(oc.is_deleted_by_user, False)
    
    def testDeleteCommentForSameUserStatus(self):
        self.client.login(username='auth_user', password='password')
        response = self.client.post('/comments/delete_comment/1/')
        self.assertEquals(response.status_code, 403)
    
    def testDeleteCommentForSameUserResult(self):
        self.client.login(username='auth_user', password='password')
        self.client.post('/comments/delete_comment/1/')
        oc = OslComment.objects.get(pk=1)
        self.assertEquals(oc.is_deleted_by_user, False)
    
    def testDeleteCommentByBannedUserStatus(self):
        ban = CommentsBannedFromIpAddress(ip_address='127.0.0.1')
        ban.save()
        self.client.login(username='jeff', password='password')
        response = self.client.post('/comments/delete_comment/1/')
        self.assertEquals(response.status_code, 403)
    
    def testDeleteCommentByBannedUserResult(self):
        ban = CommentsBannedFromIpAddress(ip_address='127.0.0.1')
        ban.save()
        self.client.login(username='jeff', password='password')
        self.client.post('/comments/delete_comment/1/')
        oc = OslComment.objects.get(pk=1)
        self.assertEquals(oc.is_deleted_by_user, False)
    
    def testDeleteCommentWithGetStatus(self):
        self.client.login(username='jeff', password='password')
        response = self.client.get('/comments/delete_comment/1/')
        self.assertEquals(response.status_code, 200)
    
    def testDeleteCommentWithGetResult(self):
        self.client.login(username='jeff', password='password')
        self.client.get('/comments/delete_comment/1/')
        oc = OslComment.objects.get(pk=1)
        self.assertEquals(oc.is_deleted_by_user, False)
    
    def testDeleteCommentWithAjaxStatus(self):
        self.client.login(username='jeff', password='password')
        response = self.client.post('/comments/delete_comment/1/', 
            HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEquals(response.status_code, 302)
    
    def testDeleteCommentWithAjaxLocation(self):
        self.client.login(username='jeff', password='password')
        response = self.client.post('/comments/delete_comment/1/', 
            HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEquals(response['location'],
            'http://testserver/comments/comment/1/')
    
    def testDeleteCommentOnNonExistantCommentStatus(self):
        self.client.login(username='jeff', password='password')
        response = self.client.post('/comments/delete_comment/1000/')
        self.assertEquals(response.status_code, 404)
    

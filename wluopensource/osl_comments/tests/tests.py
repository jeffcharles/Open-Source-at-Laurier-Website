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
    
    ## Edit comment tests ##
    
    def testNominalEditCommentStatus(self):
        self.client.login(username='jeff', password='password')
        response = self.client.post('/comments/edit/', 
            data={'comment': 'changed', 'comment_id': '1'})
        self.assertEquals(response.status_code, 302)
    
    def testNominalEditCommentLocation(self):
        self.client.login(username='jeff', password='password')
        response = self.client.post('/comments/edit/', 
            data={'comment': 'changed', 'comment_id': '1'})
        self.assertEquals(response['location'], 
            'http://testserver/comments/edited/')
    
    def testNominalEditCommentInitialValue(self):
        oc = OslComment.objects.get(pk=1)
        self.assertEquals(oc.comment, u'First!')
    
    def testNominalEditCommentResult(self):
        self.client.login(username='jeff', password='password')
        self.client.post('/comments/edit/', 
            data={'comment': 'changed', 'comment_id': '1'})
        oc = OslComment.objects.get(pk=1)
        self.assertEquals(oc.comment, u'changed')
    
    def testEditCommentAuthRequiredStatus(self):
        response = self.client.post('/comments/edit/', 
            data={'comment': 'changed', 'comment_id': '1'})
        self.assertEquals(response.status_code, 302)
        
    def testEditCommentAuthRequiredLocation(self):
        response = self.client.post('/comments/edit/', 
            data={'comment': 'changed', 'comment_id': '1'})
        self.assertEquals(response['location'], 
            'http://testserver/accounts/login/?next=/comments/edit/')
    
    def testEditCommentAuthRequiredResult(self):
        self.client.post('/comments/edit/', 
            data={'comment': 'changed', 'comment_id': '1'})
        oc = OslComment.objects.get(pk=1)
        self.assertEquals(oc.comment, u'First!')
    
    def testEditCommentForSameUserStatus(self):
        self.client.login(username='auth_user', password='password')
        response = self.client.post('/comments/edit/',
            data={'comment': 'changed', 'comment_id': '1'})
        self.assertEquals(response.status_code, 403)
    
    def testEditCommentForSameUserResult(self):
        self.client.login(username='auth_user', password='password')
        self.client.post('/comments/edit/',
            data={'comment': 'changed', 'comment_id': '1'})
        oc = OslComment.objects.get(pk=1)
        self.assertEquals(oc.comment, u'First!')
    
    def testEditCommentByBannedUserStatus(self):
        ban = CommentsBannedFromIpAddress(ip_address='127.0.0.1')
        ban.save()
        self.client.login(username='jeff', password='password')
        response = self.client.post('/comments/edit/',
            data={'comment': 'changed', 'comment_id': '1'})
        self.assertEquals(response.status_code, 400)
    
    def testEditCommentByBannedUserResult(self):
        ban = CommentsBannedFromIpAddress(ip_address='127.0.0.1')
        ban.save()
        self.client.login(username='jeff', password='password')
        self.client.post('/comments/edit/',
            data={'comment': 'changed', 'comment_id': '1'})
        oc = OslComment.objects.get(pk=1)
        self.assertEquals(oc.comment, u'First!')
    
    def testEditCommentWithGetStatus(self):
        self.client.login(username='jeff', password='password')
        response = self.client.get('/comments/edit/')
        self.assertEquals(response.status_code, 405)
    
    def testEditCommentWithGetResult(self):
        self.client.login(username='jeff', password='password')
        self.client.get('/comments/edit/')
        oc = OslComment.objects.get(pk=1)
        self.assertEquals(oc.comment, u'First!')
    
    def testEditCommentWithAjaxStatus(self):
        self.client.login(username='jeff', password='password')
        response = self.client.post('/comments/edit/',
            data={'comment': 'changed', 'comment_id': '1'}, 
            HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEquals(response.status_code, 302)
    
    def testEditCommentWithAjaxLocation(self):
        self.client.login(username='jeff', password='password')
        response = self.client.post('/comments/edit/', 
            data={'comment': 'changed', 'comment_id': '1'}, 
            HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEquals(response['location'],
            'http://testserver/comments/comment/1/')
    
    def testEditCommentPreviewStatus(self):
        self.client.login(username='jeff', password='password')
        response = self.client.post('/comments/edit/', 
            data={'comment': 'changed', 'comment_id': '1', 
            'preview': 'preview'})
        self.assertEquals(response.status_code, 200)
    
    def testEditCommentPreviewResult(self):
        self.client.login(username='jeff', password='password')
        response = self.client.post('/comments/edit/', 
            data={'comment': 'changed', 'comment_id': '1', 
            'preview': 'preview'})
        oc = OslComment.objects.get(pk=1)
        self.assertEquals(oc.comment, u'First!')
    
    def testEditCommentCancelStatus(self):
        self.client.login(username='jeff', password='password')
        response = self.client.post('/comments/edit/', 
            data={'comment': 'changed', 'comment_id': '1', 
            'cancel': 'cancel', 'cancel_url': '/cancelled/'})
        self.assertEquals(response.status_code, 302)
    
    def testEditCommentCancelLocation(self):
        self.client.login(username='jeff', password='password')
        response = self.client.post('/comments/edit/', 
            data={'comment': 'changed', 'comment_id': '1', 
            'cancel': 'cancel', 'cancel_url': '/cancelled/'})
        self.assertEquals(response['location'], 'http://testserver/cancelled/')
    
    def testEditCommentCancelResult(self):
        self.client.login(username='jeff', password='password')
        response = self.client.post('/comments/edit/', 
            data={'comment': 'changed', 'comment_id': '1', 
            'cancel': 'cancel', 'cancel_url': '/cancelled/'})
        oc = OslComment.objects.get(pk=1)
        self.assertEquals(oc.comment, u'First!')
    
    def testEditCommentDefaultTransformedComment(self):
        oc = OslComment.objects.get(pk=1)
        self.assertEquals(oc.transformed_comment, u'<p>First!</p>')
    
    def testEditCommentTransformsComment(self):
        self.client.login(username='jeff', password='password')
        self.client.post('/comments/edit/',
            data={'comment': 'changed', 'comment_id': '1'})
        oc = OslComment.objects.get(pk=1)
        self.assertEquals(oc.transformed_comment, u'<p>changed</p>')
    
    def testEditCommentUpdatesEditTimestamp(self):
        oc = OslComment.objects.get(pk=1)
        orig_edit_timestamp = oc.edit_timestamp
        
        self.client.login(username='jeff', password='password')
        self.client.post('/comments/edit/',
            data={'comment': 'changed', 'comment_id': '1'})
        
        oc = OslComment.objects.get(pk=1)
        self.assertTrue(oc.edit_timestamp > orig_edit_timestamp)
    
    def testEditCommentOnNonExistantCommentStatus(self):
        self.client.login(username='jeff', password='password')
        response = self.client.post('/comments/edit/',
            data={'comment': 'changed', 'comment_id': '1000'})
        self.assertEquals(response.status_code, 404)
    
    ## Get AJAX edit form tests ##
    
    def testGetAjaxEditForm(self):
        response = self.client.get('/comments/edit_form/1/',
            HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEquals(response.status_code, 200)
    
    def testGetAjaxEditFormForNonExistantComment(self):
        response = self.client.get('/comments/edit_form/1000/',
            HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEquals(response.status_code, 404)
    
    ## Get AJAX reply form tests ##
    
    def testGetAjaxReplyForm(self):
        response = self.client.get('/comments/reply_form/1/1/1/',
            HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEquals(response.status_code, 200)
        
    def testGetAjaxReplyFormForNonExistantComment(self):
        response = self.client.get('/comments/reply_form/1/1/1000/',
            HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEquals(response.status_code, 404)
    
    ## Get comment tests ##
    
    def testGetComment(self):
        response = self.client.get('/comments/comment/1/',
            HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEquals(response.status_code, 200)
    
    def testGetNonExistantComment(self):
        response = self.client.get('/comments/comment/1000/',
            HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEquals(response.status_code, 404)


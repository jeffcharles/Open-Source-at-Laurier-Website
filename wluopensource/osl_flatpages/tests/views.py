import os

from django.conf import settings
from django.test import TestCase
from django.test.client import Client
from osl_flatpages.models import Flatpage

class OslFlatpageTestCase(TestCase):
    fixtures = ['test_data.json']
    urls = 'osl_flatpages.tests.urls'
    
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

        self.client = Client()

    def tearDown(self):
        settings.LANGUAGES = self.old_LANGUAGES
        settings.LANGUAGE_CODE = self.old_LANGUAGE_CODE
        settings.TEMPLATE_DIRS = self.old_TEMPLATE_DIRS
    
    def test_existent(self):
        """
        Test that requesting an existing flatpage returns a 200 status code
        """
        response = self.client.get('/nontemplate/')
        self.assertEqual(response.status_code, 200)

    def test_nonexistent(self):
        """
        Test that request for non-existent page 404s
        """
        response = self.client.get('/nonexistent/')
        self.assertEqual(response.status_code, 404)
    
    def test_correct_template_loaded(self):
        """
        Test that correct template is loaded
        """
        response = self.client.get('/nontemplate/')
        self.assertTemplateUsed(response, 'osl_flatpages/display.html')
        
    def test_title(self):
        """
        Test that page title is outputting correctly
        """
        response = self.client.get('/nontemplate/')
        self.assertEqual(response.context['page'].title, 'Nontemplate title')
    
    def test_description(self):
        """
        Test that page description is outputting correctly
        """
        response = self.client.get('/nontemplate/')
        self.assertEqual(response.context['page'].description, 'Nontemplate description')
    
    def test_nontemplate_content(self):
        """
        Test that non-template content outputting correctly
        """
        response = self.client.get('/nontemplate/')
        self.assertEqual(response.context['content'], '<p>Yay a description!</p>')
    
    def test_template_content(self):
        """
        Test that template syntax is correctly interpreted
        """
        response = self.client.get('/template/')
        self.assertEqual(response.context['content'], '<p>No other stuff!</p>')
    

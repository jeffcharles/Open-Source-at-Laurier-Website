import unittest

from django.test.client import Client

class CommentsTestCase(unittest.TestCase):
    fixtures = ['comments-test-data']
    urls = 'osl_comments.tests.urls'


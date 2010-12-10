import datetime
import random
from subprocess import Popen, PIPE

from django.contrib.auth.models import User
from osl_comments.models import OslComment
from voting.models import Vote

def generate_comments(comments_to_generate, article_pk):
    """
    Generates the number of comments specified 
    
    (1 parent and 2 children comments)
    """
    u = User.objects.get(pk=1)
    for i in range(comments_to_generate / 3):
        c = OslComment(content_type_id=10, object_pk=str(article_pk), site_id=1, user_id=1, user_name='jeff', user_email='jeffrey.charles@wluopensource.org', user_url=None, comment='Something happened', submit_date=(datetime.datetime.now() + datetime.timedelta(random.randint(-1, 1))), ip_address='127.0.0.1', is_public=True, is_removed=False,  parent_comment_id=None, inline_to_object=False, edit_timestamp=datetime.datetime.now(), transformed_comment='<p>Something happened</p>', is_deleted_by_user=False)
        c.save()
        if random.randint(0, 1) == 1:
            Vote.objects.record_vote(c, u, random.randint(-1, 1))
        for j in range(2):
            c2 = OslComment(content_type_id=10, object_pk=str(article_pk), site_id=1, user_id=1, user_name='jeff', user_email='jeffrey.charles@wluopensource.org', user_url=None, comment='Something happened', submit_date=datetime.datetime.now(), ip_address='127.0.0.1', is_public=True, is_removed=False,  parent_comment_id=c.id, inline_to_object=False, edit_timestamp=(datetime.datetime.now() + datetime.timedelta(random.randint(1, 3))), transformed_comment='<p>Something happened</p>', is_deleted_by_user=False)
            c2.save()
            if random.randint(0, 1) == 1:
                Vote.objects.record_vote(c2, u, random.randint(-1, 1))

i = 10
import pdb
pdb.set_trace()
while(i <= 1000000):
    generate_comments(i, 1)
    generate_comments(i / 10, 2)
    output_process = Popen(['python', 'manage.py', 'dumpdata', 'articles', 'osl_comments.OslComment', 'voting'], stdout=PIPE)
    with open('/home/jeff/Desktop/comments_%d.json' % i, 'w') as f:
        f.write(output_process.communicate())
    i *= 10

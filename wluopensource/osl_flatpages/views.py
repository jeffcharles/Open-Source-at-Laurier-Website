from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext, Template

from osl_flatpages.models import Flatpage

def get(request, page):
    """
    Render a page for the specified page name
    """
    page_object = get_object_or_404(Flatpage, page_name=page)
    t = Template(page_object.content)
    c = RequestContext(request)
    content_html = t.render(c)
    return render_to_response('osl_flatpages/display.html',
        {'page': page_object, 'content': content_html}, 
        context_instance=RequestContext(request))

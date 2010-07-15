from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import redirect, render_to_response
from django.template import RequestContext

from accounts.forms import UserInfoChangeForm

@login_required
def profile(request):
    return render_to_response('registration/profile.html', 
        context_instance=RequestContext(request))

@login_required        
def profile_change(request):
    current_user = User.objects.get(pk=request.user.pk)
    if request.method == 'POST':
        form = UserInfoChangeForm(request.POST, instance=current_user)
        if form.is_valid():
            form.save()
            return redirect(profile)
    else:
        form = UserInfoChangeForm(instance=current_user)
    return render_to_response('registration/profile_change.html', {
        'form': form,
    }, context_instance=RequestContext(request))
        


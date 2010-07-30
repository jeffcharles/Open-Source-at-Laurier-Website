from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import redirect, render_to_response
from django.template import RequestContext

from accounts.forms import OslUserCreationForm, UserInfoChangeForm

def create_account(request):
    if request.method == 'POST':
        form = OslUserCreationForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            user = User.objects.create_user(cd['username'], cd['email'], cd['password1'])
            user.save()
            user = authenticate(username=cd['username'], password=cd['password1'])
            login(request, user)
            return redirect(profile)
    else:
        form = OslUserCreationForm()
    return render_to_response('registration/create_account.html', {
        'form': form,
    }, context_instance=RequestContext(request))

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
        

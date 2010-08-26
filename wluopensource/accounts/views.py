from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import redirect, render_to_response
from django.template import RequestContext

from accounts.forms import OslUserCreationForm, UserInfoChangeForm, UserProfileChangeForm

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
    current_profile = current_user.get_profile()
    if request.method == 'POST':
        info_form = UserInfoChangeForm(request.POST, instance=current_user)
        profile_form = UserProfileChangeForm(request.POST, instance=current_profile)
        if info_form.is_valid() and profile_form.is_valid():
            info_form.save()
            profile_form.save()
            return redirect(profile)
    else:
        info_form = UserInfoChangeForm(instance=current_user)
        profile_form = UserProfileChangeForm(instance=current_profile)
    return render_to_response('registration/profile_change.html', {
        'info_form': info_form,
        'profile_form': profile_form
    }, context_instance=RequestContext(request))
        

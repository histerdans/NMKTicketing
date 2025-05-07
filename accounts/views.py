from datetime import date

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render, get_object_or_404

from .forms import RegisterForm, UpdateForm
from .models import User


def register_page(request):
    if request.user.is_authenticated:
        return redirect('cover_page')
    else:

        form = RegisterForm()
        template_name = 'reg.html'
        if request.method == 'POST':
            form = RegisterForm(request.POST)
            if form.is_valid():
                user_profile = form.save(commit=False)
                user_profile.save()
                messages.success(request, 'User Added successfully!')
                print('SUCCESS USER ADDED')
                return redirect('accounts:login')
            context = {'form': form}
            return render(request, template_name, context)
        else:
            context = {'form': form, }
            return render(request, template_name, context)


def login_page(request):
    if request.user.is_authenticated:
        return redirect('cover_page')
    else:
        context = {}
        template = "login.html"
        if request.method == 'POST':
            username = request.POST.get('Username')
            password = request.POST.get('Password')
            # qs = User.objects.filter(username=username)
            user = authenticate(request, username=username, password=password)

            if user is not None:
                login(request, user)
                return redirect('cover_page')
            else:
                # messages.info(request, 'Username or Password is incorrect')
                messages.error(request, 'Incorrect Username or Password. Please Try again !!!')
                return render(request, template, context)
        else:
            context = {}
            return render(request, template, context)


def logout_user(request):
    logout(request)
    return redirect('/')


@login_required(login_url='accounts:login')
def table_view(request):
    context = {}
    template = "tableGL.html"
    return render(request, template, context)


@login_required
def profile_page(request, pk):
    user = get_object_or_404(User, id=pk)
    template_name = "user_profile.html"
    form = UpdateForm(instance=user)
    if request.method == 'POST':
        form = UpdateForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, 'User Updated successfully!')
            print('User Updated successfully!')
            return redirect("reminder:reminder_create_url")
        else:
            messages.error(request, 'Error User Details not Updated!')
            print('Error Occurred')
    context = {'form': form, 'user': user}
    return render(request, template_name, context)

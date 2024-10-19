from django.shortcuts import render,redirect
from .forms import UserCreateForm,DataForm
from django.contrib.auth import login,authenticate
from django.contrib.auth.decorators import login_required
from .models import *

# Create your views here.
@login_required(login_url='login')
def home(request):
    return render(request, 'home.html')

def signup(request):
    form = UserCreateForm()
    if request.method == 'POST':
        form = UserCreateForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('/')
    return render(request, 'signup.html', {'form': form})

def Login_view(request):
    if request.method == 'POST':
        user = request.POST['Username']
        Pass = request.POST['Password']
        User = authenticate(request,username=user,password=Pass)
        if User is not None:
            login(request,User)
            return redirect('home')
        else:
            return redirect('Login_view')
    return render(request,'login.html')

def ChooseBot(request):
    return render(request,'BotSelection.html')

def RuleBased(request):
    form = DataForm()
    if request.method == 'POST':
        form = DataForm(request.POST)
        form.save()
        return redirect('Datas')
    return render(request,'RuleBased.html',{'form':form})

def Datas(request):
    datas = User_ChatData.objects.all()
    return render(request,'Datas.html',{'datas':datas})
from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login',views.Login_view,name='login'),
    path('signup',views.signup,name='signup'),
    path('ChooseBot',views.ChooseBot,name='Create_Bot'),
    path('RuleBased',views.RuleBased,name='RuleBased'),
    path('Datas',views.Datas,name='Datas')
]
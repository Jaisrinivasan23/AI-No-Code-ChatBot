# yourapp/urls.py
from django.urls import path
from django.shortcuts import redirect
from .views import *
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('login/', user_login, name='login'),
    path('register/', user_register, name='register'),
    path('dashboard/<int:user_id>/', user_dashboard, name='dashboard'),
    path('chatbot/<int:chatbot_id>/', chatbot_detail, name='chatbot_detail'),
    path('delete_chatbot/<int:bot_id>/',delete_chatbot, name='delete_chatbot'),
    path('', lambda request: redirect('login')),
    path('logout/', logout_view, name='logout'),
    path('create_chatbot/', create_chatbot, name='create_chatbot'),
    path('text_file_based/', text_file_based_bot, name='text_file_based'),
    path('multi_question_chatbot/<int:chatbot_id>/',multi_question_chatbot, name='multi_question_chatbot'),
    path('select_ai_bot/<int:chatbot_id>/<str:selected_bot>/', select_ai_bot, name='select_ai_bot'),
    path('selected_bot_chat/<int:chatbot_id>/<str:bot_name>/', selected_bot_chat, name='selected_bot_chat'),
    path('create/', question_chatbot, name='Question_create'),
    path('test/<int:chatbot_id>/', test_chatbot, name='test_chatbot'),
    path('form_based_create/', form_based_bot, name='form_based'),
    path('form_based_test/<int:chatbot_id>/', test_Form_chatbot, name='form_based_test'),
    path('<str:chatbot_name>/', host_chatbot, name='host_chatbot'),
    path('<str:chatbot_name>/admin/', chatbot_admin, name='chatbot_admin')

]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


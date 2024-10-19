from django.contrib.auth.forms import UserCreationForm
from .models import *
from django.forms import ModelForm


class UserCreateForm(UserCreationForm):
    class meta:
        fields = ('username', 'email', 'password1', 'password2')
        model = User

class DataForm(ModelForm):
    class Meta:
        model = User_ChatData
        fields = '__all__'
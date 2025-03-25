from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django import forms
from .models import UserChat
class SignUpForm(UserCreationForm):
    class Meta:
        model = UserChat
        fields = ['username','password1','password2']

class LogInForm(UserCreationForm):
    class Meta:
        model = UserChat
        fields = ['username','password']


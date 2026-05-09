from django import forms
from django.contrib.auth.models import User



class RegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput())
    class Meta:
        model = User
        fields = (
            "first_name",
            "username",
            "email",
            "password1",
            "password2",
        )

class LoginForm(forms.Form):
    username = forms.CharField(label= 'Nombre de usuario')
    password = forms.CharField(label= 'Password', widget = forms.PasswordInput())

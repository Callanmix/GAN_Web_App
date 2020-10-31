from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Uploaded_Images

class DateInput(forms.DateInput):
    input_type = 'date'


class SignUpForm(UserCreationForm):
    birth_date = forms.DateField(help_text='Required. Format: YYYY-MM-DD', widget=DateInput)

    class Meta:
        model = User
        fields = ('username', 'birth_date', 'password1', 'password2', )

class image_upload_form(forms.ModelForm):
    class Meta:
        model = Uploaded_Images
        fields = ('image', 'description')
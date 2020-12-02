################################
## Imports
###############################
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Uploaded_Images, Preset_Images

#################################
## Forms
##################################
class SignUpForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('username', 'password1', 'password2', )
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder':"Username"}),
            'password1': forms.TextInput(attrs={'class': 'form-control', 'placeholder':"Password"}),
            'password2': forms.TextInput(attrs={'class': 'form-control', 'placeholder':"Confirm Password"})
        }

class image_upload_form(forms.ModelForm):
    class Meta:
        model = Preset_Images
        fields = ('image',)
        widgets = {
            'image': forms.FileInput(attrs={
                'id':"filePic",
                'accept':"image/*",
            })
        }

class Upload_New_Image_Form(forms.Form):
    image = forms.ImageField(
        label='Input Your New Image',
        widget=forms.FileInput(
            attrs={
                'id':"filePic",
                'accept':"image/*",
                'onchange':"document.getElementById('output').src = window.URL.createObjectURL(this.files[0])"
            }
        )
    )
    is_saved = forms.BooleanField(
        required=False,
        label='Do you want to save this image?',
        widget=forms.CheckboxInput(
            attrs={
                'id':"is_saved"
            }
        )
    )
    style_type = forms.CharField(
        max_length=100,
        required=True,
        label='What type of style to apply',
        widget=forms.TextInput(
            attrs={
                'id':"style_text_input",
                'placeholder':"Please Choose Style from Previous Page",
                'data-readonly': None,
                'onkeypress':"return false;",
                'oninvalid':"$('#first').trigger('click'); $('#style_alert').addClass('show');"
            }
        )
    )
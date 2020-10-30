################################
## Imports
##################################
from django.http import HttpResponse
from django.shortcuts import render, redirect

## All about logins and users
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth import logout
from django.contrib import messages

# forms
from .forms import SignUpForm

## Non Django Stuff
import os, logging
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2' 
logging.getLogger("tensorflow").setLevel(logging.ERROR)
"""
0 = all messages are logged (default behavior)
1 = INFO messages are not printed
2 = INFO and WARNING messages are not printed
3 = INFO, WARNING, and ERROR messages are not printed
"""
from tensorflow.random import normal
from tensorflow import cast, uint8
from tensorflow.keras.models import load_model
from PIL import Image
import io, base64 

#######################################
## Necessary Functions
######################################
def undo_preprocess(data):
    return data * 127.5 + 127.5

## Path To Generator
gen_path = 'C:\\Users\\calla\\Github Repos\\GAN Web App\\2_Item_32x32_GAN\\Generator'
## Load Model first to decrease load times
model = load_model(gen_path)

######################################
### Create your views here.
######################################
def home_view(request, *args, **kwargs):

    my_context = {
        'image': 'Hi'
    }

    return render(request, "home.html", my_context)


def car_horse_generator_view(request, *args, **kwargs):
    ## Use model to generate new image from random inputs
    img = cast(undo_preprocess(model(normal((1,100)), training = False)[0]), uint8)
    img = img.numpy()
    ## Convert array to jpeg
    img = Image.fromarray(img)      # Image object
    buf = io.BytesIO()              # Creat temp folder
    img.save(buf, format='JPEG')    # Save in that folder
    byte_im = buf.getvalue()        # Get Out of folder
    ## Encode as string to be received on the output
    img = base64.b64encode(byte_im).decode('utf-8')

    my_context = {
        'image': img
    }
    return render(request, "car_horse.html", my_context)


##########################################
##### This is all user_management
##########################################
def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            # Save User
            user = form.save()
            user.refresh_from_db()  # load the profile instance created by the signal
            user.profile.birth_date = form.cleaned_data.get('birth_date')
            user.save()

            print(dir(user.profile))

            # Log in
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=user.username, password=raw_password)
            login(request, user)
            return redirect('home')
    else:
        form = SignUpForm()
    return render(request, 'user_management\signup.html', {'form': form})

def logout_request(request):
    logout(request)
    return redirect('home')


def login_request(request):
    if request.method == 'POST':
        form = AuthenticationForm(request=request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.info(request, f"You are now logged in as {username}")
                return redirect('/')
            else:
                messages.error(request, "Invalid username or password.")
        else:
            messages.error(request, "Invalid username or password.")
    form = AuthenticationForm()
    return render(request = request,
                    template_name = "user_management\login.html",
                    context={"form":form})
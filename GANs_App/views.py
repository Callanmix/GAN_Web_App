################################
## Imports
##################################
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.core.files.uploadedfile import InMemoryUploadedFile

## All about logins and users
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.contrib import messages

## forms
from .forms import SignUpForm, image_upload_form, Upload_New_Image_Form

## Models
from django.contrib.auth.models import User
from .models import Uploaded_Images, Profile, MLAlgorithm, Preset_Images

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
import tflite_runtime.interpreter as tflite
from PIL import Image
import numpy as np
import io, base64, os



#########################################
## Look in Tensorflow models and add new ones
#########################################

for thing in os.listdir('Tensorflow_Models'):
    MLAlgorithm.objects.get_or_create(
        file_location = os.path.join('Tensorflow_Models', thing),
        name = thing.split('.')[0]
    )

#######################################
## Necessary Functions
######################################
def de_normalize(data):
    return data * 127.5 + 127.5
def normalize(data):
    return (data / 127.5) - 1

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def get_model(path_to_model, input_shape= (1, 256, 256, 3), output_shape= (1, 256, 256, 3)):
    """
    I am not 100% sure how Interpreter works
    Here is a link: https://www.tensorflow.org/lite/guide/python
    " To quickly run TensorFlow Lite models with Python,
    you can install just the TensorFlow Lite interpreter, 
    instead of all TensorFlow packages. "

    path_to_model:  a path to a .tflite file 
    input_shape:    a tensor for the shape of input (expects a batch size)
                    i.e. (1, 256, 256, 3) for a colored 256x256 pix image
    output_shape:    a tensor for the shape of output (expects a batch size)
                    i.e. (1, 256, 256, 3) for a colored 256x256 pix image
    """
    interpreter = tflite.Interpreter(model_path=path_to_model)
    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()
    interpreter.resize_tensor_input(input_details[0]['index'], input_shape)
    interpreter.resize_tensor_input(output_details[0]['index'], output_shape)
    interpreter.allocate_tensors()
    return interpreter, [input_details, output_details]

def make_predictions_with_tflite(model, details, array):
    """
    Not really sure what is going on with this yet
    """
    model.set_tensor(details[0][0]['index'], array)
    model.invoke()
    x = model.get_tensor(details[1][0]['index'])[0]
    return x

def generate_images(model, details, test_input): # Details is new
    ## Convert test_input to numpy
    numpy_array = np.asarray(test_input)
    numpy_array = np.expand_dims(numpy_array, axis=0)
    numpy_array = normalize(numpy_array)
    numpy_array = numpy_array.astype(np.float32)

    ## Make Style Transfer (I am not sure of how to use tensorflow lite. It works though)
    prediction = make_predictions_with_tflite(model, details, numpy_array)
    
    prediction = (prediction * 0.5 + 0.5) * 255
    prediction = prediction.astype(np.uint8)

    ## Convert Transferred to Image
    prediction = Image.fromarray(prediction)
    
    return prediction, test_input

## make html tables from db ojects
def make_tables_from_db(obj,  query_set=False, query_set_used=False):
    if query_set_used:
        if not query_set:
            return False
        object_ = query_set
        fields = [str(i).split('.')[-1] for i in obj._meta.fields]
    else:
        object_ = obj.objects.all()
        fields = [str(i).split('.')[-1] for i in obj._meta.fields]

    table = '<thead class="thead-light">\n<tr>\n'
    table += "\n".join(['<th>{}</th>'.format(field.title()) for field in fields])
    table += "</tr>\n</thead>\n"
    
    for prof in object_: 
        table += "<tr>\n"
        for field in fields:
            if field == 'image':
                table += '<td><img src="{}" style="width: 50px; height: 50px"></img></td>\n'.format(getattr(prof, field).url)
            else:
                table += '<td>{}</td>\n'.format(getattr(prof, field)) 
        table += '</tr>\n'
    return table




######################################
### Create your views here.
######################################
def home_view(request, *args, **kwargs): ## for the home page
    
    my_context = {
        'random_x': 'x'
    }
    return render(request, "home.html", my_context)

def image_upload_view(request, *args, **kwargs):
    if request.method == 'POST':
        form = image_upload_form(request.POST, request.FILES)
        if form.is_valid():
            # Get Form Data
            uploaded_image = form.save()             # Save an instance of the form

            # Get image Height and Width
            width, height = uploaded_image.image.width, uploaded_image.image.height
            
            uploaded_image.image.open()
            image_object = Image.open(uploaded_image.image)
            image_object = image_object.resize((256, 256))
            image_object.save(uploaded_image.image.path)

            # Put data into Database
            uploaded_image.refresh_from_db()                     # load the profile instance created by the signal
            uploaded_image.save()                                # Save the info into the database
            return redirect('home')
    else:
        form = image_upload_form()
    my_context = {
        'form': form
    }
    return render(request, "upload_image.html", my_context)

def image_transformation_view(request, image_id, style, *args, **kwargs):
    ############### Load Model ######################
    generator_object = MLAlgorithm.objects.get(name=style) 
    gen_input_size = eval(generator_object.model_input_size)
    gen_ouput_size = eval(generator_object.model_output_size)
    gen_path = generator_object.file_location
    model, model_details = get_model(
            gen_path,
            input_shape= gen_input_size,
            output_shape= gen_ouput_size
        )
    #######################################
    ## If id is zero is it coming from uploaded images section
    if image_id == 0:
        image_object = base64.b64decode(kwargs['encoded_image'])
        old_image = Image.open(io.BytesIO(image_object))
    ## if id is big it is a preset option. Choose a random big number as cut off because I am not planning
    ## on haveing more than a billion images
    elif image_id > 1000000000: 
        image_id = image_id - 1000000000
        image_object = Preset_Images.objects.get(id = image_id)
        ## Update Times that image has been used
        image_object.times_used += 1
        image_object.save()
        choosen_image_path = image_object.image.path
        old_image = Image.open(choosen_image_path)

    ## This is the uploaded part that individuals can choose from
    else:
        image_object = Uploaded_Images.objects.get(id = image_id)
        choosen_image_path = image_object.image.path
        old_image = Image.open(choosen_image_path)

    new_image, old_image = generate_images(model, model_details, old_image)

    my_context = {}

    for pic, name in zip([new_image, old_image], ['new_image', 'old_image']):
        buf = io.BytesIO()              # Creat temp folder
        pic.save(buf, format='JPEG')    # Save in that folder
        byte_im = buf.getvalue()        # Get Out of folder
        ## Encode as string to be received on the output
        my_context[name] = base64.b64encode(byte_im).decode('utf-8')

    return render(request, "style_gan.html", my_context)

def style_gan_image_upload_view(request, *args, **kwargs):
    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        form = Upload_New_Image_Form(request.POST or None, request.FILES or None)
        # check whether it's valid:
        if form.is_valid():
            should_save = form.cleaned_data.get('is_saved')
            selected_style = form.cleaned_data.get('style_type')
            uploaded_image_object = form.cleaned_data.get('image')
            print(type(uploaded_image_object))
            print(uploaded_image_object.name)
            print(uploaded_image_object.file)
            uploaded_image = Image.open(uploaded_image_object)
            # Get image Height and Width
            width, height = uploaded_image.width, uploaded_image.height
            uploaded_image = uploaded_image.resize((256, 256)) 
            
            buffered = io.BytesIO()
            uploaded_image.save(buffered, format="JPEG")
            byte_im = buffered.getvalue()
            encoded_image = base64.b64encode(buffered.getvalue())

            if should_save:
                new_instance = Uploaded_Images.objects.create(
                    image = InMemoryUploadedFile(buffered, None, uploaded_image_object.name, 'image/jpeg', buffered.tell, None),
                    original_height= height,
                    original_width= width,
                    uploaded_by = str(request.user.username)
                )
                new_instance.save()
            
            return image_transformation_view(request, 0, selected_style, encoded_image = encoded_image)
    else:
        form = Upload_New_Image_Form()
    
    ## Give according to permissions
    if request.user.is_superuser:
        image_object = Uploaded_Images.objects.all()
    elif request.user.is_authenticated:
        image_object = Uploaded_Images.objects.filter(uploaded_by=request.user)
    else:
        image_object = Uploaded_Images.objects.filter(uploaded_by='No.One.Will.Ever.Match.This')

    ## Presets
    preset_image_object = Preset_Images.objects.all()

    my_context = {
        'images': image_object,
        'preset_images': preset_image_object,
        'form' : form
    }
    return render(request, "choose_file_for_style_gan.html", my_context)

def basic_gan_output_view(request, style, *args, **kwargs): # test of car horse generator
    ############### Load Model ######################
    generator_object = MLAlgorithm.objects.get(name=style) 
    gen_input_size = eval(generator_object.model_input_size)
    gen_ouput_size = eval(generator_object.model_output_size)
    gen_path = generator_object.file_location
    model, model_details = get_model(
            gen_path,
            input_shape= gen_input_size,
            output_shape= gen_ouput_size
        )
    #######################################
    img = de_normalize(
        make_predictions_with_tflite(
            model,
            model_details, 
            np.array(
                np.random.normal(size=gen_input_size),
                dtype = np.float32
            )
        )
    )
    img = img.astype(np.uint8)

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
    return render(request, "basic_gan_output.html", my_context)

def basic_gans(request, *args, **kwargs): 
    my_context = {}
    return render(request, "basic_gan_page.html", my_context)


##########################################
##### This is all user_management
##########################################
def profile_page_view(request, *args, **kwargs):
    if request.user.is_superuser:
        profile_table =         make_tables_from_db(Profile)
        images_table =          make_tables_from_db(Uploaded_Images)
        algorithms_table =      make_tables_from_db(MLAlgorithm)
        preset_images_table =   make_tables_from_db(Preset_Images)


    elif request.user.is_authenticated:
        prof_object =       Profile.objects.filter(user=request.user.id)
        image_object =      Uploaded_Images.objects.filter(uploaded_by__exact = str(request.user.username))

        prof_object =       prof_object if len(prof_object) > 0 else False 
        image_object=       image_object if len(image_object) > 0 else False 
        
        profile_table =     make_tables_from_db(Profile, prof_object, query_set_used=True)
        images_table =      make_tables_from_db(Uploaded_Images, image_object, query_set_used=True)
        algorithms_table =  False
        preset_images_table=False

    else:
        profile_table =     False
        images_table =      False
        algorithms_table =  False
        preset_images_table=False

    my_context = {
        'profile_table': profile_table,
        'images_table': images_table,
        'algorithms_table': algorithms_table,
        'preset_images_table': preset_images_table
    }

    return render(request, "user_management\personal_page.html", my_context)

def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():

            # Save User
            user = form.save()
            user.refresh_from_db()  # load the profile instance created by the signal
            user.profile.birth_date = form.cleaned_data.get('birth_date')
            user.profile.ip_location = str(get_client_ip(request))
            user.save()

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
                return redirect('/')
    form = AuthenticationForm()
    return render(request = request,
                    template_name = "user_management\login.html",
                    context={"form":form})
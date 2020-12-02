from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.exceptions import ObjectDoesNotExist

class MLAlgorithm(models.Model):
    '''
    The MLAlgorithm represent the ML algorithm object.

    Attributes:
        name: The name of the algorithm.
        description: The short description of how the algorithm works.
        code: The code of the algorithm.
        version: The version of the algorithm similar to software versioning.
        owner: The name of the owner.
        created_at: The date when MLAlgorithm was added.
    ''' 
    name =              models.CharField(max_length=128)
    description =       models.TextField(max_length=2000, null=True)
    file_location =     models.CharField(max_length=300)
    model_input_size =  models.CharField(max_length=128, blank=True, null=True)
    model_output_size = models.CharField(max_length=128, blank=True, null=True)
    version =           models.CharField(max_length=128, null=True)
    created_at =        models.DateTimeField(auto_now_add=True, blank=True)

class Uploaded_Images(models.Model):
    original_height =   models.IntegerField(blank=True, null=True)
    original_width =    models.IntegerField(blank=True, null=True)
    image =             models.ImageField(upload_to='media/')
    uploaded_at =       models.DateTimeField(auto_now_add=True)
    uploaded_by =       models.CharField(max_length=100, null=True, blank=True)

class Preset_Images(models.Model):
    image =             models.ImageField(upload_to='media/preset')
    uploaded_at =       models.DateTimeField(auto_now_add=True)
    times_used =        models.IntegerField(default=0)

class Profile(models.Model):
    user =              models.OneToOneField(User, on_delete=models.CASCADE)
    ip_address =        models.CharField(max_length=30, blank=True)
    birth_date =        models.DateField(null=True, blank=True)
    created_date =      models.DateTimeField(auto_now_add=True)

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    try:
        instance.profile.save()
    except ObjectDoesNotExist:
        Profile.objects.create(user=instance)
"""GANs_Project URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth.views import LogoutView
from django.conf import settings
from django.conf.urls.static import static

from GANs_App import views

urlpatterns = [
    path('', views.home_view, name='home'), # home page
    path('admin/', admin.site.urls), #admin page
    
    path("car_horse_gen/", views.car_horse_generator_view, name="CarHorse"), # Test of Car Horse Generator
    path("upload_image/", views.image_upload_view, name="image_upload"), # Uploading Images to change

    path('signup/', views.signup), # signup page
    path("logout/", views.logout_request, name="logout"), # logout 
    path("login/", views.login_request, name="login"), # login
] + static(settings.MEDIA_URL, document_root = settings.MEDIA_ROOT)


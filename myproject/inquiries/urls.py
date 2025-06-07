from django.urls import path
from .views import create_inquiry, register_user

urlpatterns = [
    path('create/', create_inquiry, name='inquiry-create'),
    path('register/', register_user, name='register-user'),
]
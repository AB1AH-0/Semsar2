from django.urls import path
from .views import create_inquiry

urlpatterns = [
    path('create/', create_inquiry, name='inquiry-create'),
]
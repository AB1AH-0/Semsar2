from django.urls import path
from .views import create_inquiry, register_user, login_user, payment_page, process_payment

urlpatterns = [
    path('create/', create_inquiry, name='inquiry-create'),
    path('register/', register_user, name='register-user'),
    path('login/', login_user, name='login-user'),
    path('payment/', payment_page, name='payment'),
    path('process-payment/', process_payment, name='process_payment'),
]
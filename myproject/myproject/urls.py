"""
URL configuration for myproject project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
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
from django.conf import settings 
from django.conf.urls.static import static 
from django.views.generic import TemplateView

from inquiries.views import (
    register_user, new_page, create_inquiry, customers_view, get_inquiries_api,
    accept_inquiry, reject_inquiry, login_user, payment_page, process_payment, 
    logout_user, create_property, list_properties
)

urlpatterns = [
    path('admin/', admin.site.urls),

    # your inquiries API
    path('inquiries/', include('inquiries.urls')),

    # login API endpoint
    path('api/login/', login_user, name='api_login'),

    # front-end
    path('', TemplateView.as_view(template_name='home.html'),       name='home'),
    path('about/',  TemplateView.as_view(template_name='about.html'), name='about'),
    path('login/',  TemplateView.as_view(template_name='login.html'),  name='login'),
    path('register/', TemplateView.as_view(template_name='reg1.html'),  name='register'),
    path('logout/', logout_user, name='logout'),
    
    
    # User-specific pages
    path('home-user/', TemplateView.as_view(template_name='home-user.html'), name='home-user'),
    path('about-user/', TemplateView.as_view(template_name='about-user.html'), name='about-user'),
    path('property-user/', TemplateView.as_view(template_name='property-user.html'), name='property-user'),
    path('brokers/', TemplateView.as_view(template_name='brokers.html'), name='brokers'),
    
    # Broker-specific pages
    path('home-broker/', TemplateView.as_view(template_name='home-broker.html'), name='home-broker'),
    path('about-broker/', TemplateView.as_view(template_name='about-broker.html'), name='about-broker'),
    path('add-property/', TemplateView.as_view(template_name='property-broker.html'), name='add-property'),
    path('customer/', customers_view, name='customer'),
    path('payment/', payment_page, name='payment'),
    path('process_payment/', process_payment, name='process_payment'),
    
    # API endpoints
    path('api/inquiries/', create_inquiry, name='create_inquiry'),
    path('api/inquiries/list/', get_inquiries_api, name='get_inquiries'),
    path('api/inquiries/accept/', accept_inquiry, name='accept_inquiry'),
    path('api/inquiries/reject/', reject_inquiry, name='reject_inquiry'),
    path('api/properties/', create_property, name='create_property'),
    path('api/properties/list/', list_properties, name='list_properties'),
]

# Serve static files during development when DEBUG is True
if settings.DEBUG:
    # This uses the STATICFILES_DIRS setting from your settings.py
    # and serves files from the STATIC_URL path.
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0] if settings.STATICFILES_DIRS else settings.STATIC_ROOT)

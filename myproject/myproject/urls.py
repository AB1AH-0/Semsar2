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
from django.urls import path, include, reverse_lazy
from django.conf import settings # Add this import
from django.conf.urls.static import static # Add this import
from django.views.generic import TemplateView

from inquiries.views import login_user, payment_page, process_payment

urlpatterns = [
    path('admin/', admin.site.urls),

    # your inquiries API
    path('inquiries/', include('inquiries.urls')),

    # login API endpoint
    path('api/login/', login_user, name='api_login'),

    # front-end - root level
    path('', TemplateView.as_view(template_name='home.html'), name='home'),
    path('login/', TemplateView.as_view(template_name='login.html'), name='login'),
    path('register/', TemplateView.as_view(template_name='reg1.html'), name='register'),
    
    # user-specific URLs
    path('user/', include(([
        path('about/', TemplateView.as_view(template_name='User/about-user.html'), name='about'),
        path('brokers/', TemplateView.as_view(template_name='User/brokers.html'), name='brokers'),
        # Add other user-specific URLs here
    ], 'user'))),
    path('payment/', payment_page, name='payment'),
    path('process_payment/', process_payment, name='process_payment'),

    # User/Broker specific home pages
    path('broker/home/', TemplateView.as_view(template_name='Broker/home-broker.html'), name='home_broker'),
    path('user/home/', TemplateView.as_view(template_name='User/home-user.html'), name='home_user'),
]

# Serve static files during development when DEBUG is True
if settings.DEBUG:
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns
    # Serve static files from STATICFILES_DIRS
    urlpatterns += staticfiles_urlpatterns()
    # Also serve media files if needed
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

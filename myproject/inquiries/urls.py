from django.urls import path
from . import views

urlpatterns = [
    path('create/', views.create_inquiry, name='create_inquiry'),
    path('register/', views.register_user, name='register_user'),
    path('login/', views.login_user, name='login_user'),
    path('payment/', views.payment_page, name='payment_page'),
    path('process-payment/', views.process_payment, name='process_payment'),

    # API endpoints
    path('api/inquiries/broker-offers/', views.get_inquiries_api, name='get_inquiries_api'),
    path('api/inquiries/accept/', views.accept_inquiry, name='accept_inquiry'),
    path('api/inquiries/reject/', views.reject_inquiry, name='reject_inquiry'),
    path('api/deals/submit-review/', views.submit_review, name='submit_review'),
    path('api/deals/delete/<int:deal_id>/', views.delete_deal, name='delete_deal'),
    path('api/properties/', views.properties_api, name='properties_api'),
    path('api/broker-properties/', views.broker_properties_api, name='broker_properties_api'),
    path('api/broker-properties/<int:property_id>/', views.broker_properties_api, name='broker_property_detail'),
]
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import UserProfile

def register_user(request):
    if request.method == 'POST':
        user_type = request.POST.get('usertype')
        full_name = request.POST.get('full_name')
        email = request.POST.get('email')
        national_id = request.POST.get('national_id')
        phone = request.POST.get('phone')
        password = request.POST.get('password')
        license_image = request.FILES.get('license_image') if user_type == 'broker' else None

        # Create new UserProfile
        UserProfile.objects.create(
            user_type=user_type,
            full_name=full_name,
            email=email,
            national_id=national_id,
            phone=phone,
            password=password,
            license_image=license_image
        )
        
        messages.success(request, 'Registration successful!')
        return redirect('login')  # Redirect to login page after registration

    return render(request, 'reg1.html')


from .models import Inquiry

def new_page(request):
    return render(request, 'brokers.html')


@csrf_exempt
def create_inquiry(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    data = json.loads(request.body.decode() or '{}')
    inquiry = Inquiry.objects.create(
        transaction_type=data.get('transaction_type'),
        city=data.get('city-rent') or data.get('city-sale') or '',
        area=data.get('area-rent') or data.get('area-sale') or '',
        property_type=data.get('Type-rent') or data.get('Type-sale') or '',
        bedrooms=data.get('bedrooms-rent') or data.get('bedrooms-sale'),
        bathrooms=data.get('bathrooms-rent') or data.get('bathrooms-sale'),
        min_price=data.get('min_price-rent') or data.get('min_price-sale'),
        max_price=data.get('max_price-rent') or data.get('max_price-sale'),
        min_size=data.get('min_size-rent') or data.get('min_size-sale'),
        max_size=data.get('max_size-rent') or data.get('max_size-sale'),
        furnished=data.get('Furnished') in ['true', True, 'True']
    )
    return JsonResponse({'id': inquiry.id})
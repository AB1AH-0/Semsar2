import json
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import UserProfile, PaymentInfo
from django.utils import timezone

@csrf_exempt
def register_user(request):
    if request.method == 'POST':
        user_type = request.POST.get('usertype')
        full_name = request.POST.get('full_name')
        email = request.POST.get('email')
        national_id = request.POST.get('national_id')
        phone = request.POST.get('phone')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        license_image = request.FILES.get('license_image') if user_type == 'broker' else None

        errors = []

        # Check if email already exists
        if UserProfile.objects.filter(email=email).exists():
            errors.append("Email already exists")

        # Check if national ID already exists
        if UserProfile.objects.filter(national_id=national_id).exists():
            errors.append("National ID already exists")
            
        # Check if passwords match
        if password != confirm_password:
            errors.append("Passwords do not match")

        if errors:
            for error in errors:
                messages.error(request, error)
            return render(request, 'reg1.html')

        # Create new UserProfile
        user = UserProfile(
            user_type=user_type,
            full_name=full_name,
            email=email,
            national_id=national_id,
            phone=phone,
            license_image=license_image
        )
        
        # For brokers, set trial period
        if user_type == 'broker':
            user.trial_start_date = timezone.now()
            user.trial_end_date = user.trial_start_date + timezone.timedelta(days=30)
            user.has_paid = False
            
        user.set_password(password)
        user.save()
        
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

@csrf_exempt
def login_user(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    data = json.loads(request.body.decode() or '{}')
    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        return JsonResponse({'error': 'Email and password are required'}, status=400)
    
    try:
        user = UserProfile.objects.get(email=email)
    except UserProfile.DoesNotExist:
        return JsonResponse({'error': 'Invalid email or password'}, status=400)
    
    if user.check_password(password):
        from django.utils import timezone
        
        # For brokers: check trial status
        if user.user_type == 'broker':
            if not user.has_paid and (not user.trial_end_date or timezone.now() > user.trial_end_date):
                return JsonResponse({
                    'success': True,
                    'user_type': user.user_type,
                    'redirect_url': '/payment/'  # Redirect to payment view
                })
                
        return JsonResponse({
            'success': True,
            'user_type': user.user_type,
            'redirect_url': '/home-broker/' if user.user_type == 'broker' else '/home-user/'
        })
    else:
        return JsonResponse({'error': 'Invalid email or password'}, status=400)

def payment_page(request):
    return render(request, 'payment.html')

def process_payment(request):
    if request.method == 'POST':
        user_email = request.POST.get('email')
        card_holder_name = request.POST.get('name_on_card')
        card_number = request.POST.get('credit_card_number')
        exp_month = request.POST.get('exp_month')
        exp_year = request.POST.get('exp_year')
        cvv = request.POST.get('cvv')
        
        # Validate required fields
        required_fields = [user_email, card_holder_name, card_number, exp_month, exp_year, cvv]
        if not all(required_fields):
            messages.error(request, 'All payment fields are required')
            return redirect('payment')
        
        try:
            user = UserProfile.objects.get(email=user_email)
            
            # For brokers: extend trial period after payment
            if user.user_type == user.USER_TYPE_BROKER:
                user.has_paid = True
                # Set new trial end date (1 year from now)
                user.trial_end_date = timezone.now() + timezone.timedelta(days=365)
                user.save()
            
            # Create payment info record with proper encryption
            payment_info = PaymentInfo(
                user=user,
                card_holder_name=card_holder_name,
                encrypted_card_number=PaymentInfo.encrypt_value(card_number),
                encrypted_expiry_date=PaymentInfo.encrypt_value(f"{exp_month}/{exp_year}"),
                encrypted_cvv=PaymentInfo.encrypt_value(cvv)
            )
            payment_info.save()
            
            messages.success(request, 'Payment successful! Your account has been activated.')
            return redirect('home-broker.html')
        except UserProfile.DoesNotExist:
            messages.error(request, 'User not found')
        except Exception as e:
            messages.error(request, f'Payment failed: {str(e)}')
        
        return redirect('payment')
    
    return redirect('payment')
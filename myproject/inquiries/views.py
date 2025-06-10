import json
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import UserProfile, PaymentInfo, Inquiry, BrokerPost, Property
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
        return redirect('/login')  # Redirect to login page after registration

    return render(request, 'reg1.html')


def new_page(request):
    return render(request, 'brokers.html')


@csrf_exempt
def create_inquiry(request):
    """
    API endpoint to create a new inquiry from user search
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            inquiry = Inquiry.objects.create(
                transaction_type=data.get('transaction_type', 'rent'),
                city=data.get('city', ''),
                area=data.get('area', ''),
                property_type=data.get('property_type', ''),
                bedrooms=data.get('bedrooms'),
                bathrooms=data.get('bathrooms'),
                min_price=data.get('min_price'),
                max_price=data.get('max_price'),
                min_size=data.get('min_size'),
                max_size=data.get('max_size'),
                furnished=data.get('furnished', False)
            )
            
            return JsonResponse({
                'success': True,
                'inquiry_id': inquiry.id,
                'message': 'Inquiry created successfully'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)


def customers_view(request):
    """
    Display customer inquiries for brokers with broker post information
    """
    inquiries = Inquiry.objects.select_related('broker_post').all().order_by('-created_at')
    return render(request, 'customers.html', {'inquiries': inquiries})


@csrf_exempt
def get_inquiries_api(request):
    """
    API endpoint to get all inquiries as JSON
    """
    if request.method == 'GET':
        inquiries = Inquiry.objects.all().order_by('-created_at')
        inquiries_data = []
        
        for inquiry in inquiries:
            inquiry_data = {
                'id': inquiry.id,
                'city': inquiry.city or 'N/A',
                'area': inquiry.area or 'N/A',
                'property_type': inquiry.property_type or 'N/A',
                'bedrooms': inquiry.bedrooms or 'N/A',
                'bathrooms': inquiry.bathrooms or 'N/A',
                'transaction_type': inquiry.get_transaction_type_display(),
                'min_price': inquiry.min_price,
                'max_price': inquiry.max_price,
                'min_size': inquiry.min_size,
                'max_size': inquiry.max_size,
                'furnished': inquiry.furnished,
                'created_at': inquiry.created_at.strftime('%Y-%m-%d %H:%M'),
                'is_accepted': False,
                'broker_post': None
            }
            
            # Check if inquiry has been accepted (has broker post)
            if hasattr(inquiry, 'broker_post'):
                inquiry_data['is_accepted'] = True
                inquiry_data['broker_post'] = {
                    'broker_name': inquiry.broker_post.broker_name,
                    'commission': float(inquiry.broker_post.commission),
                    'notes': inquiry.broker_post.notes,
                    'accepted_at': inquiry.broker_post.created_at.strftime('%Y-%m-%d %H:%M')
                }
            
            inquiries_data.append(inquiry_data)
        
        return JsonResponse({'inquiries': inquiries_data})
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)


@csrf_exempt
def accept_inquiry(request):
    """
    API endpoint to accept an inquiry and create a broker post
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            inquiry_id = data.get('inquiry_id')
            broker_name = data.get('broker_name')
            commission = data.get('commission')
            notes = data.get('notes', '')
            
            # Validate required fields
            if not inquiry_id or not broker_name or commission is None:
                return JsonResponse({
                    'success': False,
                    'error': 'Missing required fields: inquiry_id, broker_name, and commission'
                }, status=400)
            
            inquiry = Inquiry.objects.get(id=inquiry_id)
            
            # Check if inquiry is already accepted
            if hasattr(inquiry, 'broker_post'):
                return JsonResponse({
                    'success': False,
                    'error': 'This inquiry has already been accepted'
                }, status=400)
            
            # Create broker post
            broker_post = BrokerPost.objects.create(
                inquiry=inquiry,
                broker_name=broker_name,
                commission=commission,
                notes=notes
            )
            
            return JsonResponse({
                'success': True,
                'message': f'Inquiry #{inquiry_id} accepted successfully by {broker_name}',
                'broker_post_id': broker_post.id
            })
        except Inquiry.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Inquiry not found'
            }, status=404)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)
    else:
        return JsonResponse({
            'success': False,
            'error': 'Only POST method allowed'
        }, status=405)


@csrf_exempt
def reject_inquiry(request):
    """
    API endpoint to reject an inquiry
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            inquiry_id = data.get('inquiry_id')
            
            inquiry = Inquiry.objects.get(id=inquiry_id)
            # Delete the inquiry or mark as rejected
            inquiry.delete()
            
            return JsonResponse({
                'success': True,
                'message': f'Inquiry #{inquiry_id} rejected successfully'
            })
        except Inquiry.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Inquiry not found'
            }, status=404)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)


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
                    'redirect_url': '/payment'  # Redirect to payment view
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
            return redirect('/payment')
        
        try:
            user = UserProfile.objects.get(email=user_email)
            
            # For brokers: extend trial period after payment
            if user.user_type == user.USER_TYPE_BROKER:
                user.has_paid = True
                user.trial_end_date = timezone.now() + timezone.timedelta(days=365)  # 1 year access
                user.save()
            
            # Save payment information
            payment_info = PaymentInfo(
                user=user,
                card_holder_name=card_holder_name,
                card_number=card_number[-4:],  # Only store last 4 digits
                exp_month=exp_month,
                exp_year=exp_year,
                payment_date=timezone.now()
            )
            payment_info.save()
            
            messages.success(request, 'Payment successful! Your account has been activated.')
            return redirect('/home-broker')
        except UserProfile.DoesNotExist:
            messages.error(request, 'User not found')
        except Exception as e:
            messages.error(request, f'Payment processing failed: {str(e)}')
        
        return redirect('/payment')
    
    return redirect('/payment')


def logout_user(request):
    """
    Logout view that clears session data and redirects to login page
    """
    # Clear any session data
    request.session.flush()
    
    # Add a success message
    messages.success(request, 'You have been successfully logged out.')
    
    # Redirect to login page
    return redirect('/login')


@csrf_exempt
def list_properties(request):
    """
    Debug endpoint to list all properties in the database
    """
    properties = Property.objects.all().values(
        'id', 'broker__full_name', 'transaction_type', 'city', 'area', 
        'property_type', 'price', 'created_at'
    )
    properties_list = list(properties)
    print(f"Found {len(properties_list)} properties in database")
    return JsonResponse({
        'success': True,
        'count': len(properties_list),
        'properties': properties_list
    })

@csrf_exempt
def create_property(request):
    """
    API endpoint to create a new property listing from broker form
    """
    print("\n=== New Property Creation Request ===")
    print(f"Method: {request.method}")
    print(f"Content-Type: {request.content_type}")
    
    if request.method == 'POST':
        try:
            # Print raw request body for debugging
            raw_body = request.body.decode('utf-8')
            print(f"Raw request body: {raw_body}")
            
            try:
                data = json.loads(raw_body)
                print("Parsed JSON data:", data)
            except json.JSONDecodeError as e:
                print(f"JSON decode error: {e}")
                return JsonResponse({
                    'success': False,
                    'error': 'Invalid JSON data'
                }, status=400)
            
            # Determine transaction type
            transaction_type = 'sale' if 'list-property-sale' in data else 'rent'
            print(f"Transaction type: {transaction_type}")
            
            # Get or create test broker
            try:
                broker = UserProfile.objects.filter(user_type='broker').first()
                if not broker:
                    print("Creating test broker...")
                    broker = UserProfile.objects.create(
                        user_type='broker',
                        full_name='Test Broker',
                        email='testbroker@example.com',
                        national_id='12345678901234',
                        phone='+201234567890',
                        password='testpassword123'
                    )
                    print(f"Created test broker with ID: {broker.id}")
                else:
                    print(f"Using existing broker ID: {broker.id}")
            except Exception as e:
                error_msg = f"Broker setup error: {str(e)}"
                print(error_msg)
                return JsonResponse({
                    'success': False,
                    'error': error_msg
                }, status=500)
            
            # Prepare property data
            suffix = f'-{transaction_type}'
            print(f"Using field suffix: {suffix}")
            
            # Map form fields to model fields
            field_mapping = {
                'city': f'broker-city{suffix}',
                'area': f'broker-area{suffix}',
                'property_type': f'broker-Type{suffix}',
                'bedrooms': f'broker-bedrooms{suffix}',
                'bathrooms': f'broker-bathrooms{suffix}',
                'price': f'broker-price{suffix}',
                'size': f'broker-size{suffix}',
                'furnished': f'broker-Furnished{suffix}',
            }
            
            if transaction_type == 'sale':
                field_mapping['finish'] = 'broker-Finish-sale'
            
            property_data = {'broker': broker, 'transaction_type': transaction_type}
            
            # Log field mapping
            print("\nField mapping:")
            for model_field, form_field in field_mapping.items():
                value = data.get(form_field, 'NOT FOUND')
                print(f"  {form_field} -> {model_field}: {value} (type: {type(value).__name__})")
                if value != 'NOT FOUND':
                    property_data[model_field] = value
            
            # Convert numeric fields
            for field in ['bedrooms', 'bathrooms', 'size']:
                if field in property_data:
                    try:
                        property_data[field] = int(property_data[field] or 0)
                    except (ValueError, TypeError) as e:
                        print(f"Warning: Could not convert {field} to int: {e}")
                        property_data[field] = 0
            
            # Convert price to float
            if 'price' in property_data:
                try:
                    property_data['price'] = float(property_data['price'] or 0)
                except (ValueError, TypeError) as e:
                    print(f"Warning: Could not convert price to float: {e}")
                    property_data['price'] = 0.0
            
            print("\nFinal property data:", property_data)
            
            # Create property listing
            try:
                property_listing = Property.objects.create(**property_data)
                print(f"Successfully created property listing ID: {property_listing.id}")
                
                # Verify the property exists in the database
                if Property.objects.filter(id=property_listing.id).exists():
                    print("Verified: Property exists in database")
                else:
                    print("ERROR: Property was not saved to database!")
                
                return JsonResponse({
                    'success': True,
                    'property_id': property_listing.id,
                    'message': f'Property listing created successfully! (ID: {property_listing.id})',
                    'debug': {
                        'transaction_type': transaction_type,
                        'broker_id': broker.id,
                        'broker_name': broker.full_name,
                        'fields_received': list(data.keys())
                    }
                })
                
            except Exception as e:
                error_msg = f"Error creating property: {str(e)}"
                print(error_msg)
                import traceback
                traceback.print_exc()
                return JsonResponse({
                    'success': False,
                    'error': error_msg,
                    'traceback': traceback.format_exc()
                }, status=500)
            
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            print(error_msg)
            import traceback
            traceback.print_exc()
            return JsonResponse({
                'success': False,
                'error': error_msg,
                'traceback': traceback.format_exc()
            }, status=500)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)
import json
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import UserProfile, PaymentInfo, Inquiry, BrokerPost, Property, Deal, BrokerRegistration, BrokerRejection
from django.utils import timezone
import random
import string
from django.core.files.storage import default_storage
import os
import re

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

        # Validate national ID length and numeric
        if not national_id.isdigit() or len(national_id) != 14:
            errors.append("National ID must be exactly 14 digits")

        # Validate full name (letters and spaces only)
        if not re.match(r'^[A-Za-z ]+$', full_name):
            errors.append("Full Name must contain letters and spaces only")

        # Validate phone number length and numeric
        if not phone.isdigit() or len(phone) != 11:
            errors.append("Phone Number must be exactly 11 digits")

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
        return redirect('/login/')  # Redirect to login page after registration

    return render(request, 'reg1.html')


def new_page(request):
    return render(request, 'brokers.html')


@csrf_exempt
def create_inquiry(request):
    """
    API endpoint to create a new inquiry from user search
    """
    if request.method == 'GET':
        # Delegate GET requests to the existing list endpoint logic
        return get_inquiries_api(request)

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
    
    # Get current broker information
    # TODO: Replace this with proper session-based authentication
    # For now, get the first broker or create a default one
    try:
        current_broker = UserProfile.objects.filter(user_type='broker').first()
        if not current_broker:
            # Create a default broker if none exists
            current_broker = UserProfile.objects.create(
                user_type='broker',
                full_name='Default Broker',
                email='broker@example.com',
                national_id='12345678901234',
                phone='+20 123 456 7890',
                password='defaultpassword'
            )
    except Exception as e:
        # Fallback broker data
        current_broker = {
            'full_name': 'Default Broker',
            'phone': '+20 123 456 7890'
        }
    
    context = {
        'inquiries': inquiries,
        'current_broker': current_broker
    }
    return render(request, 'customers.html', context)


@csrf_exempt
def get_inquiries_api(request):
    """
    API endpoint to get all inquiries as JSON, including broker post and deal status.
    """
    if request.method == 'GET':
        # Eager load related models to optimize queries
        inquiries = Inquiry.objects.select_related('broker_post', 'deal').all().order_by('-created_at')
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
                'broker_post': None,
                'deal_status': None, # To track the deal lifecycle
                'deal_id': None,
                'deal_rating': None,
            }
            
            # Check for associated broker post
            if hasattr(inquiry, 'broker_post'):
                inquiry_data['is_accepted'] = True
                broker_post = inquiry.broker_post
                inquiry_data['broker_post'] = {
                    'broker_name': broker_post.broker_name,
                    'commission': float(broker_post.commission),
                    'notes': broker_post.notes,
                    'media': broker_post.media,
                    'accepted_at': broker_post.created_at.strftime('%Y-%m-%d %H:%M')
                }

                # Check for associated deal, which tracks customer actions
                if hasattr(inquiry, 'deal'):
                    deal = inquiry.deal
                    inquiry_data['deal_status'] = deal.status
                    inquiry_data['deal_id'] = deal.id
                    if deal.status == 'completed':
                        inquiry_data['deal_rating'] = deal.broker_rating
                else:
                    # Broker has accepted, but customer hasn't acted yet
                    inquiry_data['deal_status'] = 'offer_pending'

            inquiries_data.append(inquiry_data)
        
        return JsonResponse({'inquiries': inquiries_data})
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)


@csrf_exempt
def accept_inquiry(request):
    """
    API endpoint to accept an inquiry and create a broker post with media.
    """
    if request.method == 'POST':
        try:
            inquiry_id = request.POST.get('inquiry_id')
            broker_name = request.POST.get('broker_name')
            broker_phone = request.POST.get('broker_phone')
            commission = request.POST.get('commission')
            notes = request.POST.get('notes', '')
            media_files = request.FILES.getlist('media')

            if not all([inquiry_id, broker_name, broker_phone, commission]):
                return JsonResponse({'success': False, 'error': 'Missing required fields'}, status=400)

            inquiry = Inquiry.objects.get(id=inquiry_id)
            if hasattr(inquiry, 'broker_post'):
                return JsonResponse({'success': False, 'error': 'This inquiry has already been accepted'}, status=400)

            media_paths = []
            for f in media_files:
                file_name = default_storage.save(f.name, f)
                media_paths.append(default_storage.url(file_name))

            broker_post = BrokerPost.objects.create(
                inquiry=inquiry,
                broker_name=broker_name,
                broker_phone=broker_phone,
                commission=commission,
                notes=notes,
                media=media_paths
            )

            return JsonResponse({
                'success': True,
                'message': f'Inquiry #{inquiry_id} accepted successfully by {broker_name}',
                'broker_post_id': broker_post.id
            })
        except Inquiry.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Inquiry not found'}, status=404)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)

    return JsonResponse({'error': 'Method not allowed'}, status=405)


@csrf_exempt
def reject_inquiry(request):
    """
    API endpoint to reject an inquiry (customer side).
    Now deletes any associated BrokerPost and Deal to ensure the offer is removed from broker listings.
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            inquiry_id = data.get('inquiry_id')
            if not inquiry_id:
                return JsonResponse({'success': False, 'error': 'Missing inquiry_id'}, status=400)

            inquiry = Inquiry.objects.get(id=inquiry_id)

            # Delete related deal first (if exists) so cascade constraints don't fail
            if hasattr(inquiry, 'deal'):
                inquiry.deal.delete()

            # Delete related broker post (if exists)
            if hasattr(inquiry, 'broker_post'):
                inquiry.broker_post.delete()

            # Finally delete the inquiry itself
            inquiry.delete()

            return JsonResponse({'success': True, 'message': f'Inquiry #{inquiry_id} rejected and removed successfully'})
        except Inquiry.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Inquiry not found'}, status=404)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)

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
    return redirect('/login/')


@csrf_exempt
def submit_review(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            deal_id = data.get('deal_id')
            rating = data.get('rating')

            if not deal_id or rating is None:
                return JsonResponse({'success': False, 'error': 'Missing deal_id or rating.'}, status=400)

            deal = Deal.objects.get(id=deal_id)
            deal.rating = int(rating)
            deal.save()

            return JsonResponse({'success': True, 'message': 'Review submitted successfully.'})
        except Deal.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Deal not found.'}, status=404)
        except (json.JSONDecodeError, ValueError, TypeError) as e:
            return JsonResponse({'success': False, 'error': f'Invalid data: {str(e)}'}, status=400)

    return JsonResponse({'error': 'Method not allowed'}, status=405)


@csrf_exempt
def delete_deal(request, deal_id):
    """
    API endpoint to delete a deal, effectively reverting an accepted offer.
    """
    if request.method == 'POST':
        try:
            deal = Deal.objects.select_related('broker_post', 'inquiry').get(id=deal_id)
            inquiry = deal.inquiry
            
            # Delete the broker_post first (which will also delete the deal due to CASCADE)
            if deal.broker_post:
                deal.broker_post.delete()
            else:
                # If there's no broker post for some reason, just delete the deal
                deal.delete()
            
            # Now delete the inquiry to remove it from customers.html
            inquiry.delete()
            
            return JsonResponse({'success': True, 'message': 'Offer and inquiry successfully deleted.'})
        except Deal.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Deal not found.'}, status=404)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)


@csrf_exempt
def properties_api(request):
    """
    API endpoint for listing and creating properties.
    - GET: Returns a list of active properties.
    - POST: Creates a new property listing.
    """
    if request.method == 'GET':
        # Optional: filter by broker id to support broker-specific lists
        broker_id = request.GET.get('broker_id')
        qs = Property.objects.filter(is_active=True)
        if broker_id:
            qs = qs.filter(broker_id=broker_id)
        properties = qs.select_related('broker').values(
            'id', 'broker__full_name', 'broker__phone', 'transaction_type', 'city', 'area',
            'property_type', 'bedrooms', 'bathrooms', 'size', 'price',
            'furnished', 'finish', 'is_active', 'created_at', 'media_files'
        )

        formatted_properties = []
        for prop in properties:
            formatted_properties.append({
                'id': prop['id'],
                'broker_name': prop['broker__full_name'],
                'broker_phone': prop['broker__phone'],
                'transaction_type': prop['transaction_type'],
                'city': prop['city'],
                'area': prop['area'],
                'property_type': prop['property_type'],
                'bedrooms': prop['bedrooms'],
                'bathrooms': prop['bathrooms'],
                'size': prop['size'],
                'price': float(prop['price']) if prop['price'] is not None else 0.0,
                'furnished': prop['furnished'],
                'finish': prop['finish'],
                'is_active': prop['is_active'],
                'images': prop['media_files'] if prop['media_files'] else [],
                'created_at': prop['created_at'].strftime('%Y-%m-%d %H:%M:%S')
            })

        return JsonResponse({
            'success': True,
            'count': len(formatted_properties),
            'properties': formatted_properties
        })

    elif request.method == 'POST':
        try:
            # Support both JSON (application/json) and file uploads (multipart/form-data)
            if request.content_type and request.content_type.startswith('multipart'):
                data = request.POST
                uploaded_files = request.FILES.getlist('media')
            else:
                data = json.loads(request.body.decode('utf-8'))
                uploaded_files = []

            transaction_type = 'sale' if 'list-property-sale' in data else 'rent'
            
            broker = UserProfile.objects.filter(user_type='broker').first()
            if not broker:
                return JsonResponse({'success': False, 'error': 'No broker account found.'}, status=400)

            suffix = f'-{transaction_type}'
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
            
            for model_field, form_field in field_mapping.items():
                value = data.get(form_field)
                if value is not None:
                    property_data[model_field] = value

            # Convert numeric fields
            for field in ['bedrooms', 'bathrooms', 'size']:
                if field in property_data and property_data[field] is not None:
                    try:
                        property_data[field] = int(property_data[field])
                    except (ValueError, TypeError):
                        property_data[field] = 0
            
            if 'price' in property_data and property_data['price'] is not None:
                try:
                    property_data['price'] = float(property_data['price'])
                except (ValueError, TypeError):
                    property_data['price'] = 0.0

            property_listing = Property.objects.create(**property_data)

            # Handle media file saving
            if uploaded_files:
                saved_paths = []
                for file_obj in uploaded_files:
                    # Save under media/property_media/<property_id>/filename
                    path = default_storage.save(
                        os.path.join('property_media', str(property_listing.id), file_obj.name),
                        file_obj
                    )
                    saved_paths.append(default_storage.url(path))
                property_listing.media_files = saved_paths
                property_listing.save(update_fields=['media_files'])

            return JsonResponse({
                'success': True,
                'property_id': property_listing.id,
                'message': f'Property listing created successfully! (ID: {property_listing.id})'
            })

        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Invalid JSON data'}, status=400)
        except Exception as e:
            import traceback
            return JsonResponse({
                'success': False, 
                'error': f'An unexpected error occurred: {str(e)}',
                'traceback': traceback.format_exc()
            }, status=500)

    return JsonResponse({'error': 'Method not allowed'}, status=405)


@csrf_exempt
def broker_properties_api(request, property_id=None):
    """
    API endpoint for brokers to manage *their* property listings.
    - GET  /api/broker-properties/ -> list current broker's properties
    - PUT  /api/broker-properties/<id>/ -> update a property
    - DELETE /api/broker-properties/<id>/ -> delete a property

    NOTE: Current implementation uses the *first* broker account in the
    database as authentication is not yet implemented. Replace with
    session-based auth when ready.
    """
    # Obtain the "current" broker (placeholder until auth is ready)
    broker = UserProfile.objects.filter(user_type='broker').first()
    if not broker:
        return JsonResponse({'success': False, 'error': 'Broker account not found.'}, status=400)

    # ------------------- LIST PROPERTIES --------------------
    if request.method == 'GET':
        props_qs = Property.objects.filter(broker=broker).values(
            'id', 'transaction_type', 'city', 'area', 'property_type',
            'bedrooms', 'bathrooms', 'size', 'price', 'furnished',
            'finish', 'is_active', 'created_at', 'media_files'
        )
        props = []
        for p in props_qs:
            props.append({
                'id': p['id'],
                'transaction_type': p['transaction_type'],
                'city': p['city'],
                'area': p['area'],
                'property_type': p['property_type'],
                'bedrooms': p['bedrooms'],
                'bathrooms': p['bathrooms'],
                'size': p['size'],
                'price': float(p['price']) if p['price'] is not None else 0.0,
                'furnished': p['furnished'],
                'finish': p['finish'],
                'is_active': p['is_active'],
                'images': p['media_files'] if p['media_files'] else [],
                'created_at': p['created_at'].strftime('%Y-%m-%d %H:%M:%S'),
            })
        return JsonResponse({'success': True, 'count': len(props), 'properties': props})

    # ------------------- UPDATE PROPERTY --------------------
    if request.method in ['PUT', 'PATCH'] and property_id is not None:
        try:
            data = json.loads(request.body.decode() or '{}')
            prop = Property.objects.get(id=property_id, broker=broker)
        except Property.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Property not found'}, status=404)
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)

        # Allowed updatable fields
        allowed = [
            'transaction_type', 'city', 'area', 'property_type', 'bedrooms',
            'bathrooms', 'size', 'price', 'furnished', 'finish', 'is_active'
        ]
        for field in allowed:
            if field in data:
                setattr(prop, field, data[field])
        prop.save()
        return JsonResponse({'success': True, 'message': 'Property updated successfully'})

    # ------------------- DELETE PROPERTY --------------------
    if request.method == 'DELETE' and property_id is not None:
        try:
            prop = Property.objects.get(id=property_id, broker=broker)
            prop.delete()
            return JsonResponse({'success': True, 'message': 'Property deleted successfully'})
        except Property.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Property not found'}, status=404)

    return JsonResponse({'error': 'Method not allowed'}, status=405)


def generate_registration_number():
    """Generate a unique broker registration number"""
    while True:
        # Generate format: BR-YYYY-XXXXXX (BR-2025-123456)
        year = timezone.now().year
        random_part = ''.join(random.choices(string.digits, k=6))
        reg_number = f"BR-{year}-{random_part}"
        
        # Check if this number already exists
        if not BrokerRegistration.objects.filter(registration_number=reg_number).exists():
            return reg_number


@csrf_exempt
def accept_broker_offer(request, inquiry_id=None):
    """
    Enhanced API endpoint for customers to accept broker offers
    Creates a Deal record and shows broker registration number
    """
    if request.method == 'POST':
        try:
            # Support both URL param and JSON body for inquiry_id
            if inquiry_id is None:
                data = json.loads(request.body or '{}')
                inquiry_id = data.get('inquiry_id')
                customer_notes = data.get('customer_notes', '')
            else:
                data = json.loads(request.body or '{}')
                customer_notes = data.get('customer_notes', '')

            if not inquiry_id:
                return JsonResponse({
                    'success': False,
                    'error': 'Missing inquiry_id'
                }, status=400)
            
            # Get the inquiry and its broker post
            inquiry = Inquiry.objects.get(id=inquiry_id)
            
            try:
                broker_post = inquiry.broker_post
            except BrokerPost.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'error': 'No broker offer found for this inquiry'
                }, status=404)
            
            # Check if deal already exists
            if hasattr(inquiry, 'deal'):
                return JsonResponse({
                    'success': False,
                    'error': 'This offer has already been accepted'
                }, status=400)
            
            # Get or create broker registration
            broker = UserProfile.objects.filter(
                full_name=broker_post.broker_name,
                user_type='broker'
            ).first()
            
            if broker:
                registration, created = BrokerRegistration.objects.get_or_create(
                    broker=broker,
                    defaults={
                        'registration_number': generate_registration_number(),
                        'registration_date': timezone.now().date(),
                        'is_active': True
                    }
                )
            else:
                # Create a default registration for unknown broker
                registration_number = generate_registration_number()
            
            # Create the deal
            deal = Deal.objects.create(
                inquiry=inquiry,
                broker_post=broker_post,
                customer_notes=customer_notes,
                status=Deal.DEAL_STATUS_PENDING,
                interview_scheduled_at=timezone.now() + timezone.timedelta(minutes=1)  # Schedule interview in 1 minute
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Broker offer accepted successfully!',
                'deal_id': deal.id,
                'broker_registration_number': registration.registration_number if broker else registration_number,
                'broker_name': broker_post.broker_name,
                'broker_phone': broker_post.broker_phone,
                'commission': float(broker_post.commission),
                'interview_scheduled_at': deal.interview_scheduled_at.isoformat(),
                'show_registration_modal': True
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
def reject_broker_offer(request, inquiry_id=None):
    """
    API endpoint for a broker to reject/withdraw an offer they have made.
    This action deletes the offer and the inquiry permanently.
    """
    if request.method == 'POST':
        try:
            if inquiry_id is None:
                try:
                    data = json.loads(request.body)
                    inquiry_id = data.get('inquiry_id')
                except (json.JSONDecodeError, AttributeError):
                    return JsonResponse({'success': False, 'error': 'Invalid request body.'}, status=400)

            if not inquiry_id:
                return JsonResponse({'success': False, 'error': 'Missing inquiry_id'}, status=400)

            inquiry = Inquiry.objects.select_related('broker_post').get(id=inquiry_id)

            # If a deal exists, it means the offer was accepted and should be deleted via the delete_deal endpoint.
            if hasattr(inquiry, 'deal'):
                return JsonResponse({
                    'success': False, 
                    'error': 'This offer has already been accepted. Please use the delete function instead.'
                }, status=400)

            # Find and delete the associated broker post
            broker_post = inquiry.broker_post
            broker_post.delete()
            
            # Delete the inquiry to remove it from customers.html
            inquiry.delete()
            
            return JsonResponse({
                'success': True,
                'message': 'Offer and inquiry successfully withdrawn.'
            })

        except Inquiry.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Inquiry not found.'}, status=404)
        except BrokerPost.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'No broker offer found for this inquiry.'}, status=404)
        except Exception as e:
            return JsonResponse({'success': False, 'error': f'An unexpected error occurred: {str(e)}'}, status=500)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)


@csrf_exempt
def submit_broker_review(request, deal_id=None):
    """
    API endpoint for customers to submit broker rating and pay commission
    """
    if request.method == 'POST':
        try:
            # Support both URL param and JSON body for deal_id
            if deal_id is None:
                data = json.loads(request.body or '{}')
                deal_id = data.get('deal_id')
            else:
                data = json.loads(request.body or '{}')

            rating = data.get('rating')
            rating_notes = data.get('rating_notes', '')
            commission_amount = data.get('commission_amount')

            if not all([deal_id, rating, commission_amount]):
                return JsonResponse({
                    'success': False,
                    'error': 'Missing required fields: deal_id, rating, commission_amount'
                }, status=400)
            
            if not (1 <= int(rating) <= 5):
                return JsonResponse({
                    'success': False,
                    'error': 'Rating must be between 1 and 5 stars'
                }, status=400)
            
            # Get the deal
            deal = Deal.objects.get(id=deal_id)
            
            # Update deal with rating and payment info
            deal.broker_rating = int(rating)
            deal.rating_notes = rating_notes
            deal.commission_amount = float(commission_amount)
            deal.commission_paid = True
            deal.status = Deal.DEAL_STATUS_COMPLETED
            deal.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Review submitted and commission paid successfully!',
                'deal_status': deal.get_status_display(),
                'rating': deal.broker_rating
            })
            
        except Deal.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Deal not found'
            }, status=404)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)


@csrf_exempt
def get_broker_rejections(request):
    """
    API endpoint for brokers to get their rejection notifications
    """
    if request.method == 'GET':
        # TODO: Get current broker from session
        # For now, get all rejections
        rejections = BrokerRejection.objects.select_related(
            'broker_post__inquiry'
        ).filter(notified=False).order_by('-created_at')
        
        rejections_data = []
        for rejection in rejections:
            rejection.broker_post.delete()
            rejections_data.append({
                'id': rejection.id,
                'inquiry_id': rejection.broker_post.inquiry.id,
                'broker_name': rejection.broker_post.broker_name,
                'customer_notes': rejection.customer_notes,
                'rejected_at': rejection.created_at.strftime('%Y-%m-%d %H:%M'),
                'inquiry_details': {
                    'city': rejection.broker_post.inquiry.city,
                    'area': rejection.broker_post.inquiry.area,
                    'property_type': rejection.broker_post.inquiry.property_type,
                    'transaction_type': rejection.broker_post.inquiry.get_transaction_type_display()
                }
            })
        
        # Mark as notified
        rejections.update(notified=True)
        
        return JsonResponse({
            'success': True,
            'rejections': rejections_data,
            'count': len(rejections_data)
        })
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)


@csrf_exempt
def get_deals_status(request):
    """
    API endpoint to get deals status for monitoring
    """
    if request.method == 'GET':
        deals = Deal.objects.select_related(
            'inquiry', 'broker_post'
        ).order_by('-created_at')
        
        deals_data = []
        for deal in deals:
            deals_data.append({
                'id': deal.id,
                'inquiry_id': deal.inquiry.id,
                'broker_name': deal.broker_post.broker_name,
                'status': deal.get_status_display(),
                'rating': deal.broker_rating,
                'commission_paid': deal.commission_paid,
                'commission_amount': float(deal.commission_amount) if deal.commission_amount else None,
                'created_at': deal.created_at.strftime('%Y-%m-%d %H:%M'),
                'interview_scheduled_at': deal.interview_scheduled_at.strftime('%Y-%m-%d %H:%M') if deal.interview_scheduled_at else None
            })
        
        return JsonResponse({
            'success': True,
            'deals': deals_data,
            'count': len(deals_data)
        })
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)


def home_broker_view(request):
    """
    Home page view for brokers with subscription days calculation
    """
    # Get current broker (for now using first broker, replace with session-based auth)
    try:
        broker = UserProfile.objects.filter(user_type=UserProfile.USER_TYPE_BROKER).first()
        
        subscription_days_left = 0
        subscription_status = "No subscription"
        
        if broker:
            if broker.has_paid:
                subscription_status = "Paid subscription"
                subscription_days_left = "∞"  # Unlimited for paid users
            elif broker.trial_end_date:
                # Calculate days left in trial
                now = timezone.now()
                if broker.trial_end_date > now:
                    days_left = (broker.trial_end_date - now).days
                    subscription_days_left = days_left
                    subscription_status = f"Trial - {days_left} days left"
                else:
                    subscription_days_left = 0
                    subscription_status = "Trial expired"
            else:
                subscription_status = "No trial started"
        
        context = {
            'broker': broker,
            'subscription_days_left': subscription_days_left,
            'subscription_status': subscription_status,
        }
        
    except Exception as e:
        context = {
            'broker': None,
            'subscription_days_left': 0,
            'subscription_status': "Error loading subscription info",
        }
    
    return render(request, 'home-broker.html', context)


@csrf_exempt
def accept_property(request, property_id=None):
    """
    API endpoint for users to accept/request a property listing.
    Creates an inquiry record for the property.
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            property_id = property_id or data.get('property_id')
            
            if not property_id:
                return JsonResponse({'success': False, 'error': 'Property ID is required.'}, status=400)
            
            # Get the property
            try:
                property_obj = Property.objects.get(id=property_id, is_active=True)
            except Property.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'Property not found or inactive.'}, status=404)
            
            # Create an inquiry for this property
            inquiry = Inquiry.objects.create(
                transaction_type=property_obj.transaction_type,
                city=property_obj.city,
                area=property_obj.area,
                property_type=property_obj.property_type,
                bedrooms=property_obj.bedrooms,
                bathrooms=property_obj.bathrooms,
                min_price=property_obj.price,
                max_price=property_obj.price,
                min_size=property_obj.size,
                max_size=property_obj.size,
                furnished=property_obj.furnished == 'Furnished',  # Convert string to boolean
                created_at=timezone.now()
            )
            
            # Create a broker post automatically for this property
            broker_post = BrokerPost.objects.create(
                inquiry=inquiry,
                broker_name=property_obj.broker.full_name,
                broker_phone=property_obj.broker.phone_number,
                commission=5.0,  # Default commission
                notes=f"Property listing request for {property_obj.property_type} in {property_obj.city}",
                created_at=timezone.now()
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Property request sent successfully!',
                'inquiry_id': inquiry.id,
                'broker_name': broker_post.broker_name,
                'broker_phone': broker_post.broker_phone
            })
            
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Invalid JSON data.'}, status=400)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)
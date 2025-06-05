import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from .models import Inquiry, Offer

@csrf_exempt
def create_inquiry(request):
    if request.method == 'GET':
        inquiries = list(Inquiry.objects.all().values())
        return JsonResponse({'inquiries': inquiries})

    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    data = json.loads(request.body.decode() or '{}')
    inquiry = Inquiry.objects.create(
        city=data.get('city-rent') or data.get('city') or '',
        area=data.get('area', ''),
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
def inquiry_detail(request, pk):
    try:
        inquiry = Inquiry.objects.get(pk=pk)
    except Inquiry.DoesNotExist:
        return JsonResponse({'error': 'Not found'}, status=404)

    if request.method == 'DELETE':
        inquiry.delete()
        return JsonResponse({'deleted': True})

    if request.method == 'POST':
        data = json.loads(request.body.decode() or '{}')
        offer = Offer.objects.create(
            inquiry=inquiry,
            price=data.get('price', 0),
            location=data.get('location', ''),
            property_type=data.get('property_type', ''),
            size=data.get('size', 0),
            bathrooms=data.get('bathrooms', 0),
            bedrooms=data.get('bedrooms', 0),
            notes=data.get('notes', '')
        )
        return JsonResponse({'offer_id': offer.id})

    return JsonResponse({'error': 'Method not allowed'}, status=405)

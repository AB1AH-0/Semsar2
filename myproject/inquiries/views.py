import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
from .models import Inquiry

def new_page(request):
    return render(request, 'Brokers.html')


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
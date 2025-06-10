#!/usr/bin/env python
import os
import sys
import django

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

from inquiries.models import Inquiry

# Create sample inquiries
try:
    # Clear existing inquiries for clean test
    Inquiry.objects.all().delete()
    
    # Create sample inquiries
    inquiry1 = Inquiry.objects.create(
        transaction_type='rent',
        city='Cairo',
        area='Nasr City',
        property_type='Apartment',
        bedrooms=3,
        bathrooms=2,
        min_price=5000,
        max_price=8000
    )
    
    inquiry2 = Inquiry.objects.create(
        transaction_type='sale',
        city='Giza',
        area='Dokki',
        property_type='Villa',
        bedrooms=4,
        bathrooms=3,
        min_price=2000000,
        max_price=3000000
    )
    
    inquiry3 = Inquiry.objects.create(
        transaction_type='rent',
        city='Cairo',
        area='Maadi',
        property_type='Studio',
        bedrooms=1,
        bathrooms=1,
        min_price=3000,
        max_price=5000
    )
    
    print(f"✅ Successfully created {Inquiry.objects.count()} sample inquiries!")
    print("Sample data:")
    for inquiry in Inquiry.objects.all():
        print(f"- ID {inquiry.id}: {inquiry.get_transaction_type_display()} {inquiry.property_type} in {inquiry.city}, {inquiry.area}")
        
except Exception as e:
    print(f"❌ Error creating sample data: {e}")

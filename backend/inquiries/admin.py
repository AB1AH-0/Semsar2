from django.contrib import admin

from .models import Inquiry, Offer

@admin.register(Inquiry)
class InquiryAdmin(admin.ModelAdmin):
    list_display = ("id", "city", "area", "property_type", "created_at")


@admin.register(Offer)
class OfferAdmin(admin.ModelAdmin):
    list_display = ("id", "inquiry", "price", "created_at")

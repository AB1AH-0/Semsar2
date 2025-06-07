from django.contrib import admin
from .models import Inquiry, UserProfile

# Register your models here.
class InquiryAdmin(admin.ModelAdmin):
    list_display = ('id', 'transaction_type', 'city', 'area', 'property_type', 'created_at')
    list_filter = ('transaction_type', 'property_type', 'city', 'created_at')
    search_fields = ('city', 'area', 'property_type')
    readonly_fields = ('created_at',)

    fieldsets = (
        (None, {
            'fields': ('transaction_type', 'city', 'area', 'property_type')
        }),
        ('Details', {
            'fields': ('bedrooms', 'bathrooms', 'min_price', 'max_price', 'min_size', 'max_size', 'furnished')
        }),
        ('Timestamps', {
            'fields': ('created_at',)
        }),
    )

admin.site.register(Inquiry, InquiryAdmin)
admin.site.register(UserProfile)

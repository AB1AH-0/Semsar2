from django.contrib import admin
from .models import Inquiry, UserProfile, PaymentLog, Property

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

class PropertyAdmin(admin.ModelAdmin):
    list_display = ('id', 'broker', 'transaction_type', 'city', 'area', 'property_type', 'price', 'created_at')
    list_filter = ('transaction_type', 'property_type', 'city', 'furnished', 'created_at')
    search_fields = ('city', 'area', 'property_type', 'broker__full_name')
    list_select_related = ('broker',)
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('broker', 'transaction_type', 'city', 'area', 'property_type')
        }),
        ('Property Details', {
            'fields': ('bedrooms', 'bathrooms', 'size', 'price', 'furnished', 'finish')
        }),
        ('Media', {
            'fields': ('media_files',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

admin.site.register(Inquiry, InquiryAdmin)
admin.site.register(UserProfile)
admin.site.register(Property, PropertyAdmin)

# New Admin class for PaymentLog
class PaymentLogAdmin(admin.ModelAdmin):
    list_display = ('id', 'broker', 'amount', 'payment_date', 'payment_method', 'status', 'transaction_id')
    list_filter = ('status', 'payment_method', 'broker', 'payment_date')
    search_fields = ('broker__full_name', 'broker__email', 'transaction_id')
    readonly_fields = ('created_at', 'updated_at', 'payment_date')
    list_per_page = 25

    fieldsets = (
        (None, {
            'fields': ('broker', 'amount', 'payment_method', 'status')
        }),
        ('Details', {
            'fields': ('transaction_id', 'notes')
        }),
        ('Timestamps', {
            'fields': ('payment_date', 'created_at', 'updated_at')
        }),
    )

    def get_queryset(self, request):
        # Ensure we only deal with brokers for the broker field
        qs = super().get_queryset(request)
        return qs.select_related('broker')

admin.site.register(PaymentLog, PaymentLogAdmin)

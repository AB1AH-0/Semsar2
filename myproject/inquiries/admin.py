from django.contrib import admin
from .models import Inquiry, UserProfile, EndUserProfile, BrokerProfile

# Register your models here.
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display    = ('id', 'full_name', 'user_type', 'email', 'national_id', 'phone', 'created_at')
    list_filter     = ('user_type',)
    readonly_fields = ('created_at',)

@admin.register(EndUserProfile)
class EndUserProfileAdmin(UserProfileAdmin):
    def get_queryset(self, request):
        return super().get_queryset(request).filter(user_type='user')

@admin.register(BrokerProfile)
class BrokerProfileAdmin(UserProfileAdmin):
    def get_queryset(self, request):
        return super().get_queryset(request).filter(user_type='broker')

@admin.register(Inquiry)
class InquiryAdmin(admin.ModelAdmin):
    list_display    = ('id', 'transaction_type', 'city', 'area', 'property_type', 'created_at')
    list_filter     = ('transaction_type', 'property_type', 'city', 'created_at')
    search_fields   = ('city', 'area', 'property_type')
    readonly_fields = ('created_at',)


@admin.register(Inquiry)
class InquiryAdmin(admin.ModelAdmin):
    list_display = ('id', 'transaction_type', 'user', 'created_at')
    readonly_fields = ('created_at',)

@admin.register(Inquiry)
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

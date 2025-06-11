from django.contrib import admin
from .models import (
    UserProfile,
    Inquiry,
    BrokerPost,
    Property,
    Deal,
    BrokerRegistration,
    BrokerRejection,
    PaymentLog
)

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'email', 'user_type', 'phone', 'has_paid', 'is_trial_active')
    list_filter = ('user_type', 'has_paid')
    search_fields = ('full_name', 'email', 'phone', 'national_id')
    readonly_fields = ('created_at', 'trial_start_date', 'trial_end_date', 'password')
    fieldsets = (
        ('Personal Info', {'fields': ('full_name', 'email', 'phone', 'national_id')}),
        ('Account Type', {'fields': ('user_type', 'license_image')}),
        ('Payment & Trial', {'fields': ('has_paid', 'trial_start_date', 'trial_end_date')}),
        ('Security', {'fields': ('password',)}),
    )

@admin.register(Inquiry)
class InquiryAdmin(admin.ModelAdmin):
    list_display = ('id', 'transaction_type', 'city', 'area', 'property_type', 'created_at')
    list_filter = ('transaction_type', 'city', 'furnished', 'property_type')
    search_fields = ('city', 'area')
    readonly_fields = ('created_at',)
    fieldsets = (
        ('Inquiry Details', {
            'fields': ('transaction_type', 'city', 'area', 'property_type', 'furnished')
        }),
        ('Property Specifications', {
            'fields': ('bedrooms', 'bathrooms', 'min_price', 'max_price', 'min_size', 'max_size')
        }),
        ('Timestamps', {
            'fields': ('created_at',)
        }),
    )

@admin.register(BrokerPost)
class BrokerPostAdmin(admin.ModelAdmin):
    list_display = ('id', 'inquiry', 'broker_name', 'commission', 'created_at')
    search_fields = ('broker_name', 'inquiry__id')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = ('id', 'broker', 'transaction_type', 'city', 'area', 'property_type', 'price', 'is_active')
    list_filter = ('transaction_type', 'property_type', 'city', 'furnished', 'is_active')
    search_fields = ('city', 'area', 'broker__full_name')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(Deal)
class DealAdmin(admin.ModelAdmin):
    list_display = ('id', 'inquiry', 'get_broker_name', 'status', 'broker_rating', 'commission_paid', 'created_at')
    list_filter = ('status', 'commission_paid')
    search_fields = ('inquiry__id', 'broker_post__broker_name')
    readonly_fields = ('created_at', 'updated_at', 'interview_scheduled_at')

    def get_broker_name(self, obj):
        return obj.broker_post.broker_name
    get_broker_name.short_description = 'Broker'

@admin.register(BrokerRegistration)
class BrokerRegistrationAdmin(admin.ModelAdmin):
    list_display = ('broker', 'registration_number', 'registration_date', 'is_active')
    search_fields = ('broker__full_name', 'registration_number')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(BrokerRejection)
class BrokerRejectionAdmin(admin.ModelAdmin):
    list_display = ('get_inquiry_id', 'get_broker_name', 'notified', 'created_at')
    search_fields = ('broker_post__broker_name', 'broker_post__inquiry__id')
    readonly_fields = ('created_at',)

    def get_inquiry_id(self, obj):
        return obj.broker_post.inquiry.id
    get_inquiry_id.short_description = 'Inquiry ID'

    def get_broker_name(self, obj):
        return obj.broker_post.broker_name
    get_broker_name.short_description = 'Broker'

@admin.register(PaymentLog)
class PaymentLogAdmin(admin.ModelAdmin):
    list_display = ('id', 'broker', 'amount', 'payment_date', 'payment_method', 'status')
    list_filter = ('status', 'payment_method', 'broker')
    search_fields = ('broker__full_name', 'transaction_id')
    readonly_fields = ('created_at', 'updated_at', 'payment_date')

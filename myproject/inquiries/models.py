from django.db import models
from django.contrib.auth.hashers import make_password, check_password

class UserProfile(models.Model):
    """
    Stores both end-users and brokers.
    Consider migrating to Django’s auth.User + a one-to-one profile
    for better password handling.
    """
    USER_TYPE_USER   = 'user'
    USER_TYPE_BROKER = 'broker'
    USER_TYPE_CHOICES = [
        (USER_TYPE_USER,   'User'),
        (USER_TYPE_BROKER, 'Broker'),
    ]

    user_type     = models.CharField(
        max_length=10,
        choices=USER_TYPE_CHOICES,
        default=USER_TYPE_USER,
        help_text="Distinguishes regular users from brokers."
    )
    full_name     = models.CharField(max_length=100)
    email         = models.EmailField(unique=True)
    national_id   = models.CharField(max_length=20, unique=True)
    phone         = models.CharField(max_length=15, unique=True)
    password      = models.CharField(
        max_length=128,
        help_text="Storing raw passwords is insecure. Consider using Django’s auth system."
    )
    
    def set_password(self, raw_password):
        self.password = make_password(raw_password)
        
    def check_password(self, raw_password):
        return check_password(raw_password, self.password)
    license_image = models.ImageField(
        upload_to='licenses/',
        blank=True,
        null=True,
        help_text="Only required when user_type='broker'."
    )
    created_at    = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'

    def __str__(self):
        return f"{self.full_name} ({self.get_user_type_display()})"
        
    def save(self, *args, **kwargs):
        # Hash password if it's provided in plain text
        if self.password and not self.password.startswith('pbkdf2_sha256$'):
            self.set_password(self.password)
        super().save(*args, **kwargs)


class EndUserProfile(UserProfile):
    """
    Proxy model for filtering only regular users in the admin.
    """
    class Meta:
        proxy = True
        verbose_name = 'User'
        verbose_name_plural = 'Users'


class BrokerProfile(UserProfile):
    """
    Proxy model for filtering only brokers in the admin.
    """
    class Meta:
        proxy = True
        verbose_name = 'Broker'
        verbose_name_plural = 'Brokers'


class Inquiry(models.Model):
    """
    Stores property-search inquiries submitted by users.
    """
    TRANSACTION_RENT = 'rent'
    TRANSACTION_SALE = 'sale'
    TRANSACTION_CHOICES = [
        (TRANSACTION_RENT, 'For Rent'),
        (TRANSACTION_SALE, 'For Sale'),
    ]

    transaction_type = models.CharField(
        max_length=4,
        choices=TRANSACTION_CHOICES,
        default=TRANSACTION_RENT,
    )
    city            = models.CharField(max_length=100, blank=True)
    area            = models.CharField(max_length=100, blank=True)
    property_type   = models.CharField(max_length=50, blank=True)
    bedrooms        = models.PositiveIntegerField(null=True, blank=True)
    bathrooms       = models.PositiveIntegerField(null=True, blank=True)
    min_price       = models.PositiveIntegerField(null=True, blank=True)
    max_price       = models.PositiveIntegerField(null=True, blank=True)
    min_size        = models.PositiveIntegerField(null=True, blank=True)
    max_size        = models.PositiveIntegerField(null=True, blank=True)
    furnished       = models.BooleanField(default=False)
    created_at      = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Inquiry'
        verbose_name_plural = 'Inquiries'

    def __str__(self):
        return (
            f"{self.get_transaction_type_display()} in {self.city or 'N/A'} – "
            f"{self.area or 'N/A'}"
        )

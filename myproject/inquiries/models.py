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
    phone         = models.CharField(max_length=15)
    password      = models.CharField(
        max_length=128,
        help_text="Storing raw passwords is insecure. Consider using Django’s auth system."
    )
    license_image = models.ImageField(
        upload_to='licenses/',
        blank=True,
        null=True,
        help_text="Only required when user_type='broker'."
    )
    created_at    = models.DateTimeField(auto_now_add=True)
    trial_start_date = models.DateTimeField(null=True, blank=True)
    trial_end_date = models.DateTimeField(null=True, blank=True)
    has_paid = models.BooleanField(default=False)

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
        
    def set_password(self, raw_password):
        self.password = make_password(raw_password)
        
    def check_password(self, raw_password):
        return check_password(raw_password, self.password)
        
    def is_trial_active(self):
        from django.utils import timezone
        if self.user_type != self.USER_TYPE_BROKER:
            return False
        if self.has_paid:
            return True
        return self.trial_end_date and timezone.now() < self.trial_end_date


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


from django.conf import settings
from cryptography.fernet import Fernet
import base64
import hashlib

class PaymentInfo(models.Model):
    """
    Stores encrypted credit card information for brokers
    """
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    card_holder_name = models.CharField(max_length=100)
    encrypted_card_number = models.BinaryField()
    encrypted_expiry_date = models.BinaryField()
    encrypted_cvv = models.BinaryField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment info for {self.user.full_name}"

    @classmethod
    def _get_cipher_suite(cls):
        # Derive a 32-byte key from SECRET_KEY
        digest = hashlib.sha256(settings.SECRET_KEY.encode()).digest()
        key = base64.urlsafe_b64encode(digest[:32])  # Fernet key must be 32 bytes
        return Fernet(key)

    @classmethod
    def encrypt_value(cls, value):
        cipher_suite = cls._get_cipher_suite()
        return cipher_suite.encrypt(value.encode())

    @classmethod
    def decrypt_value(cls, encrypted_value):
        cipher_suite = cls._get_cipher_suite()
        return cipher_suite.decrypt(encrypted_value).decode()

    def save(self, *args, **kwargs):
        # Encrypt sensitive data before saving
        if not isinstance(self.encrypted_card_number, bytes):
            self.encrypted_card_number = self.encrypt_value(self.encrypted_card_number)
        if not isinstance(self.encrypted_expiry_date, bytes):
            self.encrypted_expiry_date = self.encrypt_value(self.encrypted_expiry_date)
        if not isinstance(self.encrypted_cvv, bytes):
            self.encrypted_cvv = self.encrypt_value(self.encrypted_cvv)
        super().save(*args, **kwargs)

    @property
    def card_number(self):
        return self.decrypt_value(self.encrypted_card_number)

    @property
    def expiry_date(self):
        return self.decrypt_value(self.encrypted_expiry_date)

    @property
    def cvv(self):
        return self.decrypt_value(self.encrypted_cvv)

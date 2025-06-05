from django.db import models

class Inquiry(models.Model):
    TRANSACTION_CHOICES = [
        ('rent', 'For Rent'),
        ('sale', 'For Sale'),
    ]

    created_at = models.DateTimeField(auto_now_add=True)
    transaction_type = models.CharField(
        max_length=4,
        choices=TRANSACTION_CHOICES,
        default='rent',
        blank=False,
        null=False
    )
    city = models.CharField(max_length=100, blank=True)
    area = models.CharField(max_length=100, blank=True)
    property_type = models.CharField(max_length=50, blank=True)
    bedrooms = models.PositiveIntegerField(null=True, blank=True)
    bathrooms = models.PositiveIntegerField(null=True, blank=True)
    min_price = models.PositiveIntegerField(null=True, blank=True)
    max_price = models.PositiveIntegerField(null=True, blank=True)
    min_size = models.PositiveIntegerField(null=True, blank=True)
    max_size = models.PositiveIntegerField(null=True, blank=True)
    furnished = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.get_transaction_type_display()} - {self.city} - {self.area}"
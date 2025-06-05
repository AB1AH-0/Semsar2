from django.db import models

class Inquiry(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
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
        return f"{self.city} - {self.area}"


class Offer(models.Model):
    inquiry = models.ForeignKey(Inquiry, related_name="offers", on_delete=models.CASCADE)
    price = models.PositiveIntegerField()
    location = models.CharField(max_length=200)
    property_type = models.CharField(max_length=50)
    size = models.PositiveIntegerField()
    bathrooms = models.PositiveIntegerField()
    bedrooms = models.PositiveIntegerField()
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Offer for {self.inquiry_id} - {self.price}"

from django.db import models
from django.utils import timezone

class ReceiptFile(models.Model):
    id = models.AutoField(primary_key=True)
    file_name = models.CharField(max_length=255)
    file_path = models.CharField(max_length=500) # Full path to the stored PDF
    is_valid = models.BooleanField(default=False)
    invalid_reason = models.TextField(blank=True, null=True)
    is_processed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.file_name

    def save(self, *args, **kwargs):
        # Update updated_at on every save
        self.updated_at = timezone.now()
        super().save(*args, **kwargs)

class Receipt(models.Model):
    id = models.AutoField(primary_key=True)
    receipt_file = models.OneToOneField(ReceiptFile, on_delete=models.CASCADE, related_name='extracted_receipt')
    purchased_at = models.DateTimeField(null=True, blank=True)
    merchant_name = models.CharField(max_length=255, blank=True, null=True)
    total_amount = models.CharField(max_length=10, null=True, blank=True)
    parsed_text = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Receipt from {self.merchant_name} on {self.purchased_at}"

    def save(self, *args, **kwargs):
        self.updated_at = timezone.now()
        super().save(*args, **kwargs)
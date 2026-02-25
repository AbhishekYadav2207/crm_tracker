from django.db import models

import random
import string

def generate_short_booking_id():
    chars = string.ascii_uppercase + string.digits
    unique_part = ''.join(random.choices(chars, k=6))
    return f"BKG-{unique_part}"

class Booking(models.Model):
    STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
        ('Active', 'Active'),
        ('Completed', 'Completed'),
        ('Cancelled', 'Cancelled'),
    )
    
    booking_id = models.CharField(max_length=50, default=generate_short_booking_id, unique=True, editable=False)
    chc = models.ForeignKey('chc.CHC', on_delete=models.CASCADE, related_name='bookings')
    machine = models.ForeignKey('machines.Machine', on_delete=models.CASCADE, related_name='bookings')
    
    booking_date = models.DateTimeField(auto_now_add=True)
    start_date = models.DateField()
    end_date = models.DateField()
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    
    farmer_name = models.CharField(max_length=255)
    farmer_contact = models.CharField(max_length=10)
    farmer_email = models.EmailField()
    farmer_aadhar = models.CharField(max_length=12, help_text="12-digit Aadhar Number")
    
    field_area = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    purpose = models.TextField(blank=True, null=True)
    rejection_reason = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Booking {self.id} - {self.farmer_name}"

    class Meta:
        ordering = ['-created_at']

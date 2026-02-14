from django.db import models

class MachineUsage(models.Model):
    machine = models.ForeignKey('machines.Machine', on_delete=models.CASCADE, related_name='usage_records')
    chc = models.ForeignKey('chc.CHC', on_delete=models.CASCADE, related_name='usage_records')
    booking = models.ForeignKey('bookings.Booking', on_delete=models.SET_NULL, null=True, blank=True, related_name='usage_records')
    
    farmer_name = models.CharField(max_length=255)
    farmer_contact = models.CharField(max_length=10)
    farmer_aadhar = models.CharField(max_length=12, blank=True, null=True)
    
    usage_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    total_hours_used = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    
    # Transparency fields
    start_meter_reading = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    end_meter_reading = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    gps_lat = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    gps_lng = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    
    purpose = models.TextField(blank=True, null=True)
    crop_type = models.CharField(max_length=100, blank=True, null=True)
    area_covered = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True) # in acres
    residue_managed = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True) # in tons
    
    fuel_consumed = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True) # in liters
    operator_name = models.CharField(max_length=255, blank=True, null=True)
    remarks = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        # Auto-calculate hours if start/end time provided
        if self.start_time and self.end_time:
            # Simple calculation assuming same day usage for now, or handle date diff if needed
            # For simplicity, let's trust the input or doing simple calculation
            pass # Logic to be added in serializers or manually calculated
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Usage {self.id} - {self.machine.machine_code}"

    class Meta:
        ordering = ['-usage_date', '-start_time']

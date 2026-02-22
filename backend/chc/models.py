from django.db import models

class CHC(models.Model):
    chc_name = models.CharField(max_length=255)
    state = models.CharField(max_length=100)
    district = models.CharField(max_length=100)
    location = models.CharField(max_length=255)
    pincode = models.CharField(max_length=6)
    
    # Admin information is now managed through the User model (chc.admins)
    @property
    def admin(self):
        return self.admins.filter(role='CHC_ADMIN', is_active=True).first()

    contact_number = models.CharField(max_length=10)
    email = models.EmailField()
    
    # Auto-calculated field logic will be in signals or model methods
    total_machines = models.IntegerField(default=0)
    
    is_active = models.BooleanField(default=True)
    registration_date = models.DateTimeField(auto_now_add=True)
    
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    def __str__(self):
        return f"{self.chc_name} ({self.district})"

    class Meta:
        ordering = ['-registration_date']

from django.db import models

class Machine(models.Model):
    MACHINE_TYPES = (
        ('Happy Seeder', 'Happy Seeder'),
        ('Super Seeder', 'Super Seeder'),
        ('Smart Seeder', 'Smart Seeder'),
        ('Mulcher', 'Mulcher'),
        ('Rotavator', 'Rotavator'),
        ('Zero Tillage Drill', 'Zero Tillage Drill'),
        ('Straw Baler', 'Straw Baler'),
        ('Straw Reaper', 'Straw Reaper'),
        ('Straw Chopper', 'Straw Chopper'),
        ('Paddy Thresher', 'Paddy Thresher'),
        ('Wheat Thresher', 'Wheat Thresher'),
        ('Chaff Cutter', 'Chaff Cutter'),
        ('Disc Harrow', 'Disc Harrow'),
        ('Cultivator', 'Cultivator'),
        ('Laser Land Leveller', 'Laser Land Leveller'),
        ('Reaper Binder', 'Reaper Binder'),
        ('Baler', 'Baler'),
        ('Rake', 'Rake'),
        ('Straw Collection Machine', 'Straw Collection Machine'),
        ('Other', 'Other'),
    )

    STATUS_CHOICES = (
        ('Idle', 'Idle'),
        ('In Use', 'In Use'),
        ('Maintenance', 'Maintenance'),
        ('Out of Service', 'Out of Service'),
    )

    machine_code = models.CharField(max_length=100, unique=True)
    machine_name = models.CharField(max_length=255)
    machine_type = models.CharField(max_length=50, choices=MACHINE_TYPES)
    purchase_year = models.IntegerField()
    funding_source = models.CharField(max_length=255, blank=True, null=True, help_text="Scheme Name or Funding Source")
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Idle')
    chc = models.ForeignKey('chc.CHC', on_delete=models.CASCADE, related_name='machines')
    
    def save(self, *args, **kwargs):
        if not self.machine_code:
            # Generate a simple code: CHC_ID-TYPE-COUNT
            # We need to save first to get ID if we want global ID, but we want CHC specific count
            count = Machine.objects.filter(chc=self.chc).count() + 1
            type_code = self.machine_type[:3].upper()
            self.machine_code = f"{self.chc.id}-{type_code}-{count}"
            
            # Ensure uniqueness loop just in case
            while Machine.objects.filter(machine_code=self.machine_code).exists():
                count += 1
                self.machine_code = f"{self.chc.id}-{type_code}-{count}"
                
        super().save(*args, **kwargs)
    
    total_hours_used = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    last_used_date = models.DateTimeField(null=True, blank=True)
    last_serviced_date = models.DateField(null=True, blank=True)
    next_service_due = models.DateField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.machine_name} ({self.machine_code})"

    class Meta:
        ordering = ['-created_at']

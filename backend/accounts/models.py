from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    ROLE_CHOICES = (
        ('CHC_ADMIN', 'CHC Administrator'),
        ('GOVT_ADMIN', 'Government Administrator'),
    )
    
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='CHC_ADMIN')
    # We use a string reference for 'chc.CHC' to avoid circular imports or import errors before the app is ready
    chc = models.ForeignKey('chc.CHC', on_delete=models.SET_NULL, null=True, blank=True, related_name='admins')
    phone_no = models.CharField(max_length=10, blank=True, null=True)
    designation = models.CharField(max_length=100, blank=True, null=True)
    
    # Required for unique constraints if we want to enforce unique phone/email
    email = models.EmailField(unique=True)

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

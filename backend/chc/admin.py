from django.contrib import admin
from .models import CHC

@admin.register(CHC)
class CHCAdmin(admin.ModelAdmin):
    list_display = ('chc_name', 'state', 'district', 'contact_number', 'is_active')
    list_filter = ('state', 'district', 'is_active')
    search_fields = ('chc_name', 'contact_number', 'email')

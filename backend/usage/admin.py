from django.contrib import admin
from .models import MachineUsage

@admin.register(MachineUsage)
class MachineUsageAdmin(admin.ModelAdmin):
    list_display = ('machine', 'chc', 'usage_date', 'farmer_name', 'total_hours_used')
    list_filter = ('usage_date', 'chc')
    search_fields = ('machine__machine_name', 'farmer_name')

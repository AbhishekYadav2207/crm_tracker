from django.contrib import admin
from .models import Machine

@admin.register(Machine)
class MachineAdmin(admin.ModelAdmin):
    list_display = ('machine_code', 'machine_name', 'machine_type', 'chc', 'status')
    list_filter = ('machine_type', 'status', 'chc')
    search_fields = ('machine_code', 'machine_name')

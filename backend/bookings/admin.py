from django.contrib import admin
from .models import Booking

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('booking_id', 'farmer_name', 'machine', 'chc', 'start_date', 'end_date', 'status')
    list_filter = ('status', 'start_date', 'chc')
    search_fields = ('booking_id', 'farmer_name', 'farmer_contact')

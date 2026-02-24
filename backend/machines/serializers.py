from rest_framework import serializers
from .models import Machine

class MachineSerializer(serializers.ModelSerializer):
    chc_details = serializers.SerializerMethodField()
    active_booking = serializers.SerializerMethodField()
    
    class Meta:
        model = Machine
        fields = '__all__'
        read_only_fields = ('machine_code', 'created_at', 'updated_at', 'total_hours_used')

    def get_chc_details(self, obj):
        return {
            "id": obj.chc.id,
            "name": obj.chc.chc_name,
            "district": obj.chc.district
        }

    def get_active_booking(self, obj):
        if obj.status == 'In Use':
            # Import Booking here to avoid circular dependencies
            from bookings.models import Booking
            active_booking = Booking.objects.filter(machine=obj, status='Active').first()
            if active_booking:
                return {
                    "booking_id": str(active_booking.booking_id),
                    "farmer_name": active_booking.farmer_name,
                    "farmer_contact": active_booking.farmer_contact,
                    "start_date": active_booking.start_date,
                    "end_date": active_booking.end_date,
                    "status": active_booking.status
                }
        return None

    def validate_status(self, value):
        if self.instance:
            old_status = self.instance.status
            new_status = value
            
            # Allow same status
            if old_status == new_status:
                return value
                
            # From In Use
            if old_status == 'In Use' and new_status == 'Idle':
                # Generally we want this done via booking completion, but if forced, we should check
                from bookings.models import Booking
                if Booking.objects.filter(machine=self.instance, status='Active').exists():
                    raise serializers.ValidationError("Cannot change status to Idle directly while there is an active booking. Complete the booking first.")
                    
        return value

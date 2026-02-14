from rest_framework import serializers
from .models import Booking
from machines.serializers import MachineSerializer
from chc.serializers import CHCSerializer

class BookingSerializer(serializers.ModelSerializer):
    machine_details = MachineSerializer(source='machine', read_only=True)
    chc_details = CHCSerializer(source='chc', read_only=True)

    class Meta:
        model = Booking
        fields = '__all__'
        read_only_fields = ('booking_status', 'created_at', 'updated_at', 'rejection_reason', 'approved_by')

class BookingCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = ('id', 'booking_id', 'machine', 'start_date', 'end_date', 'farmer_name', 'farmer_contact', 'farmer_email', 'farmer_aadhar', 'purpose', 'field_area')
        read_only_fields = ('id', 'booking_id')

    def validate(self, data):
        if data['start_date'] > data['end_date']:
            raise serializers.ValidationError("End date must be after start date.")
        # Check machine availability logic here or in view
        return data

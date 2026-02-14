from rest_framework import serializers
from .models import MachineUsage

class MachineUsageSerializer(serializers.ModelSerializer):
    class Meta:
        model = MachineUsage
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at', 'total_hours_used', 'chc')

    def validate(self, data):
        # Additional validations if needed
        return data

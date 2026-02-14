from rest_framework import serializers
from .models import Machine

class MachineSerializer(serializers.ModelSerializer):
    chc_details = serializers.SerializerMethodField()
    
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

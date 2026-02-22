from rest_framework import serializers
from .models import CHC

class CHCSerializer(serializers.ModelSerializer):
    admin_name = serializers.SerializerMethodField()

    class Meta:
        model = CHC
        fields = '__all__'

    def get_admin_name(self, obj):
        admin = obj.admin
        return admin.get_full_name() if admin else None

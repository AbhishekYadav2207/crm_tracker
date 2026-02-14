from rest_framework import serializers
from .models import CHC

class CHCSerializer(serializers.ModelSerializer):
    class Meta:
        model = CHC
        fields = '__all__'

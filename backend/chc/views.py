from rest_framework import generics, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import CHC
from .serializers import CHCSerializer

class IsGovtAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'GOVT_ADMIN'

class PublicCHCSearchView(generics.ListAPIView):
    queryset = CHC.objects.filter(is_active=True)
    serializer_class = CHCSerializer
    permission_classes = (permissions.AllowAny,)
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['pincode', 'district', 'state']
    search_fields = ['chc_name', 'location']

class CHCListCreateView(generics.ListCreateAPIView):
    queryset = CHC.objects.all()
    serializer_class = CHCSerializer
    
    def get_permissions(self):
        if self.request.method == 'POST':
            # Only GOVT_ADMIN can create CHC
            return [permissions.IsAuthenticated(), IsGovtAdmin()]
        return [permissions.IsAuthenticated()] 

class CHCDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = CHC.objects.all()
    serializer_class = CHCSerializer
    
    def get_permissions(self):
        if self.request.method in ['DELETE', 'PUT', 'PATCH']:
            # Require GOVT_ADMIN to modify/delete CHC
            return [permissions.IsAuthenticated(), IsGovtAdmin()]
        return [permissions.IsAuthenticated()]

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.contrib.auth import get_user_model

User = get_user_model()

class AssignAdminView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsGovtAdmin]

    def post(self, request, pk):
        chc = get_object_or_404(CHC, pk=pk)
        admin_id = request.data.get('admin_id')
        
        if not admin_id:
            return Response({"error": "Admin ID is required"}, status=status.HTTP_400_BAD_REQUEST)
            
        with transaction.atomic():
            new_admin = get_object_or_404(User, id=admin_id, role='CHC_ADMIN')
            
            # Detach any existing admins for this CHC
            existing_admins = User.objects.filter(chc=chc, role='CHC_ADMIN')
            for admin in existing_admins:
                admin.chc = None
                # Optional: admin.is_active = False if they strictly leave the system
                admin.save()
            
            new_admin.chc = chc
            new_admin.is_active = True
            new_admin.save()
            
        return Response({"message": "Admin assigned successfully", "admin_name": new_admin.get_full_name()})

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
    permission_classes = (permissions.IsAuthenticated,)

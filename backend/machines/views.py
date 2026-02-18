from rest_framework import generics, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import Machine
from .serializers import MachineSerializer
from rest_framework.exceptions import PermissionDenied

class PublicMachineListView(generics.ListAPIView):
    queryset = Machine.objects.select_related('chc').all()
    serializer_class = MachineSerializer
    permission_classes = (permissions.AllowAny,)
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['chc', 'machine_type', 'status']
    search_fields = ['machine_name']

class DetailedMachineView(generics.RetrieveAPIView):
    queryset = Machine.objects.all()
    serializer_class = MachineSerializer
    permission_classes = (permissions.AllowAny,)

class CHCMachineListCreateView(generics.ListCreateAPIView):
    serializer_class = MachineSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return Machine.objects.none()
        if user.role == 'CHC_ADMIN' and user.chc:
            return Machine.objects.select_related('chc').filter(chc=user.chc)
        elif user.role == 'GOVT_ADMIN':
            return Machine.objects.select_related('chc').all()
        return Machine.objects.none()

    def perform_create(self, serializer):
        user = self.request.user
        if user.role == 'CHC_ADMIN' and user.chc:
            serializer.save(chc=user.chc)
        else:
            raise PermissionDenied("You must be a CHC Admin to add machines.")

class CHCMachineDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = MachineSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return Machine.objects.none()
        if user.role == 'CHC_ADMIN' and user.chc:
            return Machine.objects.filter(chc=user.chc)
        return Machine.objects.none()

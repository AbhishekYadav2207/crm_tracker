from rest_framework import generics, permissions
from .models import MachineUsage
from .serializers import MachineUsageSerializer

class MachineUsageListCreateView(generics.ListCreateAPIView):
    serializer_class = MachineUsageSerializer
    permission_classes = (permissions.IsAuthenticated,)
    filterset_fields = ['machine', 'chc', 'booking']

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return MachineUsage.objects.none()
        if user.role == 'CHC_ADMIN' and user.chc:
            return MachineUsage.objects.filter(chc=user.chc)
        elif user.role == 'GOVT_ADMIN':
            return MachineUsage.objects.all()
        return MachineUsage.objects.none()

    def perform_create(self, serializer):
        user = self.request.user
        if user.role == 'CHC_ADMIN' and user.chc:
            serializer.save(chc=user.chc)
        else:
            raise PermissionDenied("You must be a CHC Admin to record usage.")

class MachineUsageDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = MachineUsageSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return MachineUsage.objects.none()
        if user.role == 'CHC_ADMIN' and user.chc:
            return MachineUsage.objects.filter(chc=user.chc)
        elif user.role == 'GOVT_ADMIN':
            return MachineUsage.objects.all()
        return MachineUsage.objects.none()

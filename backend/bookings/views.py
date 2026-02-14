from rest_framework import generics, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import Booking
from .serializers import BookingSerializer, BookingCreateSerializer
from rest_framework.response import Response
from rest_framework import status
from analytics.models import AuditLog, Notification

class PublicBookingCreateView(generics.CreateAPIView):
    queryset = Booking.objects.all()
    serializer_class = BookingCreateSerializer
    permission_classes = (permissions.AllowAny,)

    def perform_create(self, serializer):
        machine = serializer.validated_data['machine']
        serializer.save(status='Pending', chc=machine.chc)
        # Here we should convert BookingCreateSerializer to BookingSerializer for response if needed
        # Or trigger notifications

class PublicBookingStatusView(generics.RetrieveAPIView):
    queryset = Booking.objects.all()
    serializer_class = BookingSerializer
    permission_classes = (permissions.AllowAny,)
    lookup_field = 'booking_id' # Assuming we expose internal ID or add a UUID field

class CHCBookingListView(generics.ListAPIView):
    serializer_class = BookingSerializer
    permission_classes = (permissions.IsAuthenticated,)
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status', 'machine']
    ordering_fields = ['booking_date', 'start_date']

    def get_queryset(self):
        user = self.request.user
        if user.role == 'CHC_ADMIN' and user.chc:
            return Booking.objects.filter(chc=user.chc)
        return Booking.objects.none()

class CHCBookingActionView(generics.UpdateAPIView):
    queryset = Booking.objects.all()
    serializer_class = BookingSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def update(self, request, *args, **kwargs):
        booking = self.get_object()
        action = request.data.get('action') # approve or reject
        notes = request.data.get('notes', '')
        
        if booking.chc != request.user.chc:
            return Response({"error": "Not authorized"}, status=status.HTTP_403_FORBIDDEN)

        if action == 'approve':
            booking.status = 'Approved'
            booking.approved_by = request.user
            # Check availability again logic
        elif action == 'reject':
            booking.status = 'Rejected'
            booking.rejection_reason = notes
            booking.approved_by = request.user
        else:
            return Response({"error": "Invalid action"}, status=status.HTTP_400_BAD_REQUEST)
        
        booking.save()
        
        # Log Audit
        AuditLog.objects.create(
            user=request.user,
            action_type=action.upper(),
            table_name='bookings',
            record_id=str(booking.id),
            new_value={'status': booking.status, 'notes': notes}
        )
        
        return Response(BookingSerializer(booking).data)

from rest_framework import generics, permissions, filters, serializers
from django_filters.rest_framework import DjangoFilterBackend
from .models import Booking
from .serializers import BookingSerializer, BookingCreateSerializer
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from analytics.models import AuditLog, Notification

class PublicBookingCreateView(generics.CreateAPIView):
    queryset = Booking.objects.all()
    serializer_class = BookingCreateSerializer
    permission_classes = (permissions.AllowAny,)

    def perform_create(self, serializer):
        machine = serializer.validated_data['machine']
        start_date = serializer.validated_data['start_date']
        end_date = serializer.validated_data['end_date']
        
        # Availability Check
        overlapping_bookings = Booking.objects.filter(
            machine=machine,
            status__in=['Pending', 'Approved', 'Active'],
            start_date__lte=end_date,
            end_date__gte=start_date
        )
        
        if overlapping_bookings.exists():
             raise serializers.ValidationError("Machine is not available for the selected dates.")

        serializer.save(status='Pending', chc=machine.chc)
        # Here we should convert BookingCreateSerializer to BookingSerializer for response if needed
        # Or trigger notifications

class PublicBookingStatusView(generics.RetrieveAPIView):
    queryset = Booking.objects.all()
    serializer_class = BookingSerializer
    permission_classes = (permissions.AllowAny,)
    lookup_field = 'booking_id'

class CHCBookingListView(generics.ListAPIView):
    serializer_class = BookingSerializer
    permission_classes = (permissions.IsAuthenticated,)
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
    filterset_fields = ['machine']
    ordering_fields = ['booking_date', 'start_date', 'farmer_name', 'status']
    search_fields = ['farmer_name', 'farmer_contact', 'booking_id', 'machine__machine_name']

    def get_queryset(self):
        user = self.request.user
        if not (user.role == 'CHC_ADMIN' and user.chc):
            return Booking.objects.none()
            
        queryset = Booking.objects.filter(chc=user.chc)
        
        # 1. Custom Filtering by start_date, end_date
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date:
            queryset = queryset.filter(start_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(end_date__lte=end_date)
            
        machine_type = self.request.query_params.get('machine_type')
        if machine_type:
            queryset = queryset.filter(machine__machine_type=machine_type)
            
        # 2. Categorization Logic
        category = self.request.query_params.get('category')
        if category == 'Pending':
            queryset = queryset.filter(status='Pending')
        elif category == 'Active':
            # Assuming 'Approved' and 'Active' bookings are considered Active in Categorization logic.
            # Active tabs usually list bookings ready to be handed over or currently in use
            queryset = queryset.filter(status__in=['Approved', 'Active'])
        elif category == 'Completed':
            queryset = queryset.filter(status__in=['Completed', 'Cancelled', 'Rejected'])

        # 3. Custom Sorting Mapping
        sort_param = self.request.query_params.get('sort')
        if sort_param == 'booking_date_latest':
            queryset = queryset.order_by('-booking_date')
        elif sort_param == 'booking_date_oldest':
            queryset = queryset.order_by('booking_date')
        elif sort_param == 'farmer_name_asc':
            queryset = queryset.order_by('farmer_name')
        elif sort_param == 'farmer_name_desc':
            queryset = queryset.order_by('-farmer_name')
            
        return queryset

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
        elif action == 'handover':
            if booking.status != 'Approved':
                return Response({"error": "Only approved bookings can be handed over."}, status=status.HTTP_400_BAD_REQUEST)
            booking.status = 'Active'
            booking.machine.status = 'In Use'
            booking.machine.save()
            # Could set actual_start_time here
        elif action == 'complete':
            if booking.status != 'Active':
                 return Response({"error": "Only active bookings can be completed."}, status=status.HTTP_400_BAD_REQUEST)
            booking.status = 'Completed'
            booking.machine.status = 'Idle'
            booking.machine.save()
            # Could set actual_end_time here
        elif action == 'cancel':
            booking.status = 'Cancelled'
            booking.rejection_reason = notes # Reuse for cancellation reason
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

class MachineBookedDatesView(APIView):
    permission_classes = (permissions.AllowAny,)

    def get(self, request, machine_id):
        bookings = Booking.objects.filter(
            machine_id=machine_id,
            status__in=['Pending', 'Approved', 'Active']
        ).values('start_date', 'end_date')
        
        return Response(list(bookings))

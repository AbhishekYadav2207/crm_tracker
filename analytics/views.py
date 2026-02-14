from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from django.db.models import Count, Sum, Avg
from machines.models import Machine
from bookings.models import Booking
from usage.models import MachineUsage
from chc.models import CHC

class GovtDashboardView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        if request.user.role != 'GOVT_ADMIN':
            return Response({"error": "Unauthorized"}, status=403)
        
        total_chcs = CHC.objects.filter(is_active=True).count()
        total_machines = Machine.objects.count()
        total_bookings = Booking.objects.count()
        total_usage_hours = MachineUsage.objects.aggregate(Sum('total_hours_used'))['total_hours_used__sum'] or 0
        total_residue_managed = MachineUsage.objects.aggregate(Sum('residue_managed'))['residue_managed__sum'] or 0
        total_area_covered = MachineUsage.objects.aggregate(Sum('area_covered'))['area_covered__sum'] or 0

        return Response({
            "total_chcs": total_chcs,
            "total_machines": total_machines,
            "total_bookings": total_bookings,
            "total_usage_hours": total_usage_hours,
            "total_residue_managed": total_residue_managed,
            "total_area_covered": total_area_covered
        })

class CHCDashboardView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        user = request.user
        if user.role != 'CHC_ADMIN' or not user.chc:
            return Response({"error": "Unauthorized"}, status=403)
        
        chc = user.chc
        machines = Machine.objects.filter(chc=chc)
        bookings = Booking.objects.filter(chc=chc)
        
        return Response({
            "total_machines": machines.count(),
            "machines_available": machines.filter(status='Idle').count(),
            "machines_in_use": machines.filter(status='In Use').count(),
            "pending_bookings": bookings.filter(status='Pending').count(),
            "active_bookings": bookings.filter(status='Active').count(),
        })


class MachineAnalyticsView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        # Role check
        if request.user.role not in ['GOVT_ADMIN', 'CHC_ADMIN']:
             return Response({"error": "Unauthorized"}, status=403)

        # Detailed stats about machines
        machine_types = Machine.objects.values('machine_type').annotate(count=Count('id'))

        status_breakdown = Machine.objects.values('status').annotate(count=Count('id'))
        
        return Response({
            "machine_types": machine_types,
            "status_breakdown": status_breakdown,
        })

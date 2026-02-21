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
        
        # 1. Overall Key Metrics
        total_chcs = CHC.objects.filter(is_active=True).count()
        total_machines = Machine.objects.count()
        total_bookings = Booking.objects.count()
        total_usage_hours = MachineUsage.objects.aggregate(Sum('total_hours_used'))['total_hours_used__sum'] or 0
        total_residue_managed = MachineUsage.objects.aggregate(Sum('residue_managed'))['residue_managed__sum'] or 0
        total_area_covered = MachineUsage.objects.aggregate(Sum('area_covered'))['area_covered__sum'] or 0

        # 2. Charts Data (State-Wide)
        # Status Breakdown (Active/Idle/Maintenance)
        status_breakdown_qs = Machine.objects.values('status').annotate(count=Count('id'))
        status_breakdown = {item['status']: item['count'] for item in status_breakdown_qs}
        
        # Machine Type Breakdown
        machine_types_qs = Machine.objects.values('machine_type').annotate(count=Count('id'))
        machine_types = {item['machine_type']: item['count'] for item in machine_types_qs}

        # 3. CHC-Wise Analytics (Leaderboard Matrix)
        # Calculate active machine count per CHC, usage hours, area, and residue
        chcs = CHC.objects.filter(is_active=True)
        chc_metrics = []
        for chc in chcs:
            chc_id = chc.id
            chc_machines = Machine.objects.filter(chc=chc)
            chc_total_machines = chc_machines.count()
            chc_active_machines = chc_machines.filter(status='In Use').count()
            
            chc_bookings = Booking.objects.filter(chc=chc)
            chc_total_bookings = chc_bookings.count()
            chc_active_bookings = chc_bookings.filter(status='Active').count()
            
            chc_usage = MachineUsage.objects.filter(chc=chc)
            c_hours = chc_usage.aggregate(Sum('total_hours_used'))['total_hours_used__sum'] or 0
            c_area = chc_usage.aggregate(Sum('area_covered'))['area_covered__sum'] or 0
            c_residue = chc_usage.aggregate(Sum('residue_managed'))['residue_managed__sum'] or 0
            
            chc_metrics.append({
                "chc_id": chc_id,
                "chc_name": chc.chc_name,
                "district": chc.district,
                "total_machines": chc_total_machines,
                "active_machines": chc_active_machines,
                "total_bookings": chc_total_bookings,
                "active_bookings": chc_active_bookings,
                "total_hours": c_hours,
                "area_covered": c_area,
                "residue_managed": c_residue
            })

        return Response({
            "overview": {
                "total_chcs": total_chcs,
                "total_machines": total_machines,
                "total_bookings": total_bookings,
                "total_usage_hours": total_usage_hours,
                "total_residue_managed": total_residue_managed,
                "total_area_covered": total_area_covered
            },
            "charts": {
                "status_breakdown": status_breakdown,
                "machine_types": machine_types
            },
            "chc_analytics": chc_metrics
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

class GovtCHCDetailedAnalyticsView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, chc_id):
        if request.user.role != 'GOVT_ADMIN':
            return Response({"error": "Unauthorized"}, status=403)

        try:
            chc = CHC.objects.get(id=chc_id)
        except CHC.DoesNotExist:
            return Response({"error": "CHC not found"}, status=404)

        # Basic Info
        chc_info = {
            "id": chc.id,
            "name": chc.chc_name,
            "district": chc.district,
            "admin": chc.admin_name,
            "contact": chc.contact_number
        }

        # Machines
        machines_qs = Machine.objects.filter(chc=chc)
        machines_data = []
        for m in machines_qs:
            # Get latest usage
            latest_usage = m.usage_records.order_by('-usage_date').first()
            machines_data.append({
                "id": m.id,
                "name": m.machine_name,
                "type": m.machine_type,
                "code": m.machine_code,
                "status": m.status,
                "hours": float(m.total_hours_used),
                "last_serviced": m.last_serviced_date,
                "last_used": latest_usage.usage_date if latest_usage else None
            })

        # Recent Bookings
        bookings_qs = Booking.objects.filter(chc=chc).order_by('-created_at')[:10]
        bookings_data = [{
            "id": b.id,
            "farmer": b.farmer_name,
            "machine": b.machine.machine_name if b.machine else "N/A",
            "start_date": b.start_date,
            "end_date": b.end_date,
            "status": b.status
        } for b in bookings_qs]

        # Usage History (Recent 10)
        usage_qs = MachineUsage.objects.filter(chc=chc).order_by('-usage_date', '-start_time')[:10]
        usage_data = [{
            "id": u.id,
            "machine": u.machine.machine_name if u.machine else "N/A",
            "farmer": u.farmer_name,
            "date": u.usage_date,
            "hours": float(u.total_hours_used) if u.total_hours_used else 0,
            "area": float(u.area_covered) if u.area_covered else 0
        } for u in usage_qs]

        return Response({
            "chc_info": chc_info,
            "machines": machines_data,
            "recent_bookings": bookings_data,
            "recent_usage": usage_data
        })

class GovtReportsView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        if request.user.role != 'GOVT_ADMIN':
            return Response({"error": "Unauthorized"}, status=403)

        # Generate Insights for the Reports Page
        
        # 1. Provide district wise aggregation
        district_data = CHC.objects.values('district').annotate(
            total_chcs=Count('id', distinct=True)
        )
        
        district_performance = []
        for d in district_data:
            dist = d['district']
            chcs_in_district = CHC.objects.filter(district=dist)
            
            # Aggregate machines
            machines = Machine.objects.filter(chc__in=chcs_in_district)
            total_machines = machines.count()
            idle_machines = machines.filter(status='Idle').count()
            
            # Aggregate usage
            usage = MachineUsage.objects.filter(chc__in=chcs_in_district)
            hours = usage.aggregate(Sum('total_hours_used'))['total_hours_used__sum'] or 0
            area = usage.aggregate(Sum('area_covered'))['area_covered__sum'] or 0
            
            district_performance.append({
                "district": dist,
                "chcs": d['total_chcs'],
                "machines": total_machines,
                "idle_machines": idle_machines,
                "hours": float(hours),
                "area": float(area)
            })

        # 2. Recommendations (Basic Logic)
        recommendations = []
        # Find districts with high idle machines but low hours
        for dp in district_performance:
            if dp['machines'] > 0:
                idle_ratio = dp['idle_machines'] / dp['machines']
                if idle_ratio > 0.5:
                    recommendations.append({
                        "type": "warning",
                        "message": f"{dp['district']} has {idle_ratio*100:.0f}% idle equipment ({dp['idle_machines']} machines). Consider promotional campaigns or migrating equipment to high-demand areas."
                    })
            if dp['hours'] > (dp['machines'] * 100): # simplistic high usage threshold
                 recommendations.append({
                        "type": "success",
                        "message": f"{dp['district']} is showing exceptionally high utilization of its {dp['machines']} machines. Consider allocating more funds or equipment here."
                 })

        if not recommendations:
             recommendations.append({
                 "type": "info",
                 "message": "Equipment utilization is currently balanced across districts. No critical migrations required."
             })

        return Response({
            "district_performance": district_performance,
            "recommendations": recommendations
        })

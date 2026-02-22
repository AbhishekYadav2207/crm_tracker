import os
import sys
import json
from datetime import datetime, date
from decimal import Decimal
from pathlib import Path

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm_backend.settings')  # Change this to your project name

import django
django.setup()

# Now import your models
from django.contrib.auth import get_user_model
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models

from accounts.models import User
from chc.models import CHC
from machines.models import Machine
from bookings.models import Booking
from usage.models import MachineUsage
from analytics.models import AuditLog, Notification

class ExtendedJSONEncoder(DjangoJSONEncoder):
    """Extended JSON encoder to handle additional types."""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        if isinstance(obj, models.Model):
            return str(obj)
        return super().default(obj)

def serialize_queryset(queryset, fields=None):
    """Convert queryset to list of dictionaries."""
    data = []
    for obj in queryset:
        obj_dict = {}
        for field in obj._meta.fields:
            field_name = field.name
            field_value = getattr(obj, field_name)
            
            # Handle foreign keys
            if field.is_relation:
                if field_value:
                    obj_dict[field_name] = {
                        'id': field_value.id,
                        'str': str(field_value)
                    }
                else:
                    obj_dict[field_name] = None
            else:
                obj_dict[field_name] = field_value
        
        # Add string representation
        obj_dict['__str__'] = str(obj)
        data.append(obj_dict)
    return data

def export_to_json(output_dir='exported_data'):
    """Export all data to JSON files."""
    
    # Create output directory
    Path(output_dir).mkdir(exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    print(f"📤 Exporting data to {output_dir}/ ...")
    
    # Export Users
    print("  Exporting Users...")
    users = User.objects.all().select_related('chc')
    user_data = []
    for user in users:
        user_dict = {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'password': '🔒 HASHED - Use reset if needed',  # Don't export actual password
            'role': user.role,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'phone_no': user.phone_no,
            'designation': user.designation,
            'is_staff': user.is_staff,
            'is_active': user.is_active,
            'date_joined': user.date_joined.isoformat() if user.date_joined else None,
            'last_login': user.last_login.isoformat() if user.last_login else None,
            'chc': {
                'id': user.chc.id,
                'name': user.chc.chc_name
            } if user.chc else None,
            '__str__': str(user)
        }
        user_data.append(user_dict)
    
    with open(f'{output_dir}/users_{timestamp}.json', 'w', encoding='utf-8') as f:
        json.dump(user_data, f, indent=2, cls=ExtendedJSONEncoder, ensure_ascii=False)
    
    # Create a separate credentials file with login info
    credentials = []
    for user in users:
        cred = {
            'username': user.username,
            'email': user.email,
            'role': user.role,
            'chc': user.chc.chc_name if user.chc else None,
            'default_password': 'admin123' if 'admin' in user.username else 'password123',  # Based on your population script
            'login_url': '/admin/' if user.is_staff else '/dashboard/',
            'notes': 'Use "Forgot Password" if default password doesn\'t work'
        }
        credentials.append(cred)
    
    with open(f'{output_dir}/credentials_{timestamp}.json', 'w', encoding='utf-8') as f:
        json.dump(credentials, f, indent=2, ensure_ascii=False)
    
    # Export CHCs
    print("  Exporting CHCs...")
    chcs = CHC.objects.all()
    chc_data = serialize_queryset(chcs)
    with open(f'{output_dir}/chcs_{timestamp}.json', 'w', encoding='utf-8') as f:
        json.dump(chc_data, f, indent=2, cls=ExtendedJSONEncoder, ensure_ascii=False)
    
    # Export Machines
    print("  Exporting Machines...")
    machines = Machine.objects.all().select_related('chc')
    machine_data = []
    for machine in machines:
        machine_dict = {
            'id': machine.id,
            'machine_code': machine.machine_code,
            'machine_name': machine.machine_name,
            'machine_type': machine.machine_type,
            'status': machine.status,
            'purchase_year': machine.purchase_year,
            'funding_source': machine.funding_source,
            'total_hours_used': float(machine.total_hours_used) if machine.total_hours_used else 0,
            'last_used_date': machine.last_used_date.isoformat() if machine.last_used_date else None,
            'last_serviced_date': machine.last_serviced_date.isoformat() if machine.last_serviced_date else None,
            'next_service_due': machine.next_service_due.isoformat() if machine.next_service_due else None,
            'chc': {
                'id': machine.chc.id,
                'name': machine.chc.chc_name
            },
            'created_at': machine.created_at.isoformat() if machine.created_at else None,
            'updated_at': machine.updated_at.isoformat() if machine.updated_at else None,
            '__str__': str(machine)
        }
        machine_data.append(machine_dict)
    
    with open(f'{output_dir}/machines_{timestamp}.json', 'w', encoding='utf-8') as f:
        json.dump(machine_data, f, indent=2, cls=ExtendedJSONEncoder, ensure_ascii=False)
    
    # Export Bookings
    print("  Exporting Bookings...")
    bookings = Booking.objects.all().select_related('chc', 'machine')
    booking_data = []
    for booking in bookings:
        booking_dict = {
            'id': booking.id,
            'booking_id': str(booking.booking_id),
            'status': booking.status,
            'farmer_name': booking.farmer_name,
            'farmer_contact': booking.farmer_contact,
            'farmer_email': booking.farmer_email,
            'farmer_aadhar': booking.farmer_aadhar[-4:].rjust(12, '*'),  # Mask Aadhaar
            'field_area': float(booking.field_area) if booking.field_area else None,
            'purpose': booking.purpose,
            'rejection_reason': booking.rejection_reason,
            'start_date': booking.start_date.isoformat() if booking.start_date else None,
            'end_date': booking.end_date.isoformat() if booking.end_date else None,
            'booking_date': booking.booking_date.isoformat() if booking.booking_date else None,
            'created_at': booking.created_at.isoformat() if booking.created_at else None,
            'updated_at': booking.updated_at.isoformat() if booking.updated_at else None,
            'chc': {
                'id': booking.chc.id,
                'name': booking.chc.chc_name
            },
            'machine': {
                'id': booking.machine.id,
                'code': booking.machine.machine_code,
                'name': booking.machine.machine_name
            },
            '__str__': str(booking)
        }
        booking_data.append(booking_dict)
    
    with open(f'{output_dir}/bookings_{timestamp}.json', 'w', encoding='utf-8') as f:
        json.dump(booking_data, f, indent=2, cls=ExtendedJSONEncoder, ensure_ascii=False)
    
    # Export Usage Records
    print("  Exporting Usage Records...")
    usages = MachineUsage.objects.all().select_related('machine', 'chc', 'booking')
    usage_data = []
    for usage in usages:
        usage_dict = {
            'id': usage.id,
            'usage_date': usage.usage_date.isoformat() if usage.usage_date else None,
            'start_time': str(usage.start_time) if usage.start_time else None,
            'end_time': str(usage.end_time) if usage.end_time else None,
            'total_hours_used': float(usage.total_hours_used) if usage.total_hours_used else None,
            'farmer_name': usage.farmer_name,
            'farmer_contact': usage.farmer_contact,
            'area_covered': float(usage.area_covered) if usage.area_covered else None,
            'crop_type': usage.crop_type,
            'residue_managed': float(usage.residue_managed) if usage.residue_managed else None,
            'fuel_consumed': float(usage.fuel_consumed) if usage.fuel_consumed else None,
            'operator_name': usage.operator_name,
            'remarks': usage.remarks,
            'start_meter_reading': float(usage.start_meter_reading) if usage.start_meter_reading else None,
            'end_meter_reading': float(usage.end_meter_reading) if usage.end_meter_reading else None,
            'gps_lat': float(usage.gps_lat) if usage.gps_lat else None,
            'gps_lng': float(usage.gps_lng) if usage.gps_lng else None,
            'created_at': usage.created_at.isoformat() if usage.created_at else None,
            'machine': {
                'id': usage.machine.id,
                'code': usage.machine.machine_code
            },
            'chc': {
                'id': usage.chc.id,
                'name': usage.chc.chc_name
            },
            'booking_id': usage.booking.id if usage.booking else None,
            '__str__': str(usage)
        }
        usage_data.append(usage_dict)
    
    with open(f'{output_dir}/usages_{timestamp}.json', 'w', encoding='utf-8') as f:
        json.dump(usage_data, f, indent=2, cls=ExtendedJSONEncoder, ensure_ascii=False)
    
    # Export Audit Logs (sampled)
    print("  Exporting Audit Logs (last 1000)...")
    audit_logs = AuditLog.objects.all().order_by('-timestamp')[:1000].select_related('user')
    audit_data = []
    for log in audit_logs:
        log_dict = {
            'id': log.id,
            'action_type': log.action_type,
            'table_name': log.table_name,
            'record_id': log.record_id,
            'ip_address': log.ip_address,
            'timestamp': log.timestamp.isoformat() if log.timestamp else None,
            'user': str(log.user) if log.user else None,
            'user_id': log.user.id if log.user else None,
            'old_value': log.old_value,
            'new_value': log.new_value,
            '__str__': str(log)
        }
        audit_data.append(log_dict)
    
    with open(f'{output_dir}/audit_logs_{timestamp}.json', 'w', encoding='utf-8') as f:
        json.dump(audit_data, f, indent=2, cls=ExtendedJSONEncoder, ensure_ascii=False)
    
    # Export Notifications
    print("  Exporting Notifications...")
    notifications = Notification.objects.all().select_related('user')
    notification_data = []
    for note in notifications:
        note_dict = {
            'id': note.id,
            'title': note.title,
            'message': note.message,
            'notification_type': note.notification_type,
            'related_url': note.related_url,
            'is_read': note.is_read,
            'created_at': note.created_at.isoformat() if note.created_at else None,
            'user': {
                'id': note.user.id,
                'username': note.user.username,
                'email': note.user.email
            } if note.user else None,
            '__str__': str(note)
        }
        notification_data.append(note_dict)
    
    with open(f'{output_dir}/notifications_{timestamp}.json', 'w', encoding='utf-8') as f:
        json.dump(notification_data, f, indent=2, cls=ExtendedJSONEncoder, ensure_ascii=False)
    
    # Create summary report
    summary = {
        'export_timestamp': timestamp,
        'statistics': {
            'users': User.objects.count(),
            'chcs': CHC.objects.count(),
            'machines': Machine.objects.count(),
            'bookings': Booking.objects.count(),
            'usages': MachineUsage.objects.count(),
            'audit_logs': AuditLog.objects.count(),
            'notifications': Notification.objects.count(),
        },
        'user_roles': {
            'GOVT_ADMIN': User.objects.filter(role='GOVT_ADMIN').count(),
            'CHC_ADMIN': User.objects.filter(role='CHC_ADMIN').count(),
        },
        'machine_status': dict(Machine.objects.values_list('status').annotate(count=models.Count('id'))),
        'booking_status': dict(Booking.objects.values_list('status').annotate(count=models.Count('id'))),
        'sample_credentials': credentials[:10]  # First 10 credentials
    }
    
    with open(f'{output_dir}/summary_{timestamp}.json', 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    
    # Create a README file
    readme_content = f"""# Data Export - {timestamp}

## 📊 Database Statistics
- Total Users: {summary['statistics']['users']}
- Total CHCs: {summary['statistics']['chcs']}
- Total Machines: {summary['statistics']['machines']}
- Total Bookings: {summary['statistics']['bookings']}
- Total Usage Records: {summary['statistics']['usages']}
- Total Audit Logs: {summary['statistics']['audit_logs']}
- Total Notifications: {summary['statistics']['notifications']}

## 🔐 Login Credentials
Default passwords from population script:
- Admin users: password = "admin123"
- Staff users: password = "password123"
- Government admins: password = "Govt@123456"

### Sample Users:
"""
    
    for cred in credentials[:20]:
        readme_content += f"""
- **{cred['username']}** ({cred['role']})
  - Email: {cred['email']}
  - CHC: {cred['chc']}
  - Default Password: {cred['default_password']}
  - Login URL: {cred['login_url']}
"""
    
    readme_content += """

## 📁 Exported Files
- users_[timestamp].json - All user accounts
- credentials_[timestamp].json - Login credentials only
- chcs_[timestamp].json - All CHCs
- machines_[timestamp].json - All machines
- bookings_[timestamp].json - All bookings
- usages_[timestamp].json - All usage records
- audit_logs_[timestamp].json - Last 1000 audit logs
- notifications_[timestamp].json - All notifications
- summary_[timestamp].json - Summary statistics

## 🔍 How to Login
1. Go to your Django admin panel at `/admin/` or login page at `/login/`
2. Use any username/email from the credentials file
3. Use the default password shown above
4. If password doesn't work, use the "Forgot Password" feature

## ⚠️ Notes
- Aadhaar numbers are masked in the export for privacy
- Passwords are not exported (only placeholders)
- For superuser access, create one with `python manage.py createsuperuser`
"""
    
    with open(f'{output_dir}/README_{timestamp}.txt', 'w', encoding='utf-8') as f:
        f.write(readme_content)
    
    print(f"\n✅ Export completed successfully!")
    print(f"📁 Files saved in: {output_dir}/")
    print(f"📄 Check README_{timestamp}.txt for login credentials")
    print(f"🔐 Credentials file: credentials_{timestamp}.json")

if __name__ == '__main__':
    # Change the output directory if needed
    export_to_json('latest_data')
import os
import django
from datetime import date, timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm_backend.settings')
django.setup()

from django.contrib.auth import get_user_model
from chc.models import CHC
from machines.models import Machine
from bookings.models import Booking

User = get_user_model()

def populate():
    print("Populating data...")

    # Create Superuser (Govt Admin)
    if not User.objects.filter(username='govt_admin').exists():
        User.objects.create_superuser('govt_admin', 'admin@govt.in', 'admin123', role='GOVT_ADMIN')
        print("Created Govt Admin: govt_admin/admin123")

    # Create CHC
    chc, created = CHC.objects.get_or_create(
        chc_name="Green Valley CHC",
        defaults={
            "state": "Punjab",
            "district": "Ludhiana",
            "location": "Village Raikot",
            "pincode": "141109",
            "admin_name": "Rajinder Singh",
            "contact_number": "9876543210",
            "email": "chc.green@example.com",
            "total_machines": 5
        }
    )
    if created:
        print(f"Created CHC: {chc.chc_name}")

    # Create CHC Admin User
    if not User.objects.filter(username='chc_admin').exists():
        User.objects.create_user('chc_admin', 'chc@example.com', 'admin123', role='CHC_ADMIN', chc=chc)
        print("Created CHC Admin: chc_admin/admin123")

    # Create Machines
    machines_data = [
        {"code": "M-001", "name": "Standard Happy Seeder", "type": "Happy Seeder", "year": 2023, "funding": "SMAM"},
        {"code": "M-002", "name": "Super Seeder 2024", "type": "Super Seeder", "year": 2024, "funding": "CROP_RES_MGT"},
        {"code": "M-003", "name": "Baler Max", "type": "Baler", "year": 2022, "funding": "STATE_SUB"},
    ]

    for m_data in machines_data:
        machine, created = Machine.objects.get_or_create(
            machine_code=m_data['code'],
            defaults={
                "machine_name": m_data['name'],
                "machine_type": m_data['type'],
                "purchase_year": m_data['year'],
                "funding_source": m_data['funding'],
                "chc": chc,
                "status": "Idle"
            }
        )
        if created:
            print(f"Created Machine: {machine.machine_name}")

    # Create Bookings
    m1 = Machine.objects.get(machine_code="M-001")
    Booking.objects.get_or_create(
        machine=m1,
        start_date=date.today() + timedelta(days=1),
        end_date=date.today() + timedelta(days=3),
        defaults={
            "chc": chc,
            "farmer_name": "Gurpreet Singh",
            "farmer_contact": "9988776655",
            "farmer_email": "farmer@example.com",
            "farmer_aadhar": "123456789012",
            "status": "Pending",
            "field_area": 5.5,
            "purpose": "Sowing Wheat"
        }
    )
    print("Created Sample Booking")

    print("Data population complete.")

if __name__ == '__main__':
    populate()

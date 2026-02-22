import os
import django
import json
import random
from datetime import date, timedelta, datetime
from faker import Faker  # Using faker for realistic names/addresses if available, else fallback

# Setup Django Environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm_backend.settings')
django.setup()

from django.contrib.auth import get_user_model
from chc.models import CHC
from machines.models import Machine
from bookings.models import Booking
from usage.models import MachineUsage

User = get_user_model()
fake = Faker('en_IN')  # Indian locale

def create_users():
    users_created = []
    
    # Govt Admin
    if not User.objects.filter(username='govt_admin').exists():
        User.objects.create_superuser('govt_admin', 'admin@govt.in', 'admin123', role='GOVT_ADMIN')
        users_created.append({"username": "govt_admin", "role": "GOVT_ADMIN", "password": "admin123"})
    
    return users_created

def create_chcs():
    chc_data_list = [
        {"name": "Ludhiana Central CHC", "district": "Ludhiana", "state": "Punjab", "loc": "Gill Road", "pin": "141001"},
        {"name": "Patiala Farmers Hub", "district": "Patiala", "state": "Punjab", "loc": "Nabha Road", "pin": "147001"},
        {"name": "Jalandhar Agri Care", "district": "Jalandhar", "state": "Punjab", "loc": "Model Town", "pin": "144003"},
        {"name": "Amritsar Green Seva", "district": "Amritsar", "state": "Punjab", "loc": "Batala Road", "pin": "143001"},
        {"name": "Bathinda Crop Solutions", "district": "Bathinda", "state": "Punjab", "loc": "Goniana Mandi", "pin": "151001"},
    ]

    created_chcs = []

    for data in chc_data_list:
        admin_name = fake.name()
        phone = f"98{fake.msisdn()[2:10]}"
        email = f"chc.{data['district'].lower()}@example.com"
        
        chc, created = CHC.objects.get_or_create(
            chc_name=data['name'],
            defaults={
                "state": data['state'],
                "district": data['district'],
                "location": data['loc'],
                "pincode": data['pin'],
                "contact_number": phone,
                "email": email,
                "total_machines": 0
            }
        )
        
        # Create CHC Admin
        username = f"admin_{data['district'].lower()}"
        if not User.objects.filter(username=username).exists():
           User.objects.create_user(username, email, 'admin123', role='CHC_ADMIN', chc=chc, first_name=admin_name.split()[0])
        
        created_chcs.append(chc)
    
    return created_chcs

def create_machines(chcs):
    machine_types = ['Happy Seeder', 'Super Seeder', 'Mulcher', 'MB Plough', 'Rotavator', 'Baler']
    statuses = ['Idle', 'Idle', 'In Use', 'Maintenance', 'Idle'] # Weighted towards Idle
    
    created_machines = []
    
    for chc in chcs:
        num_machines = random.randint(5, 12)
        for i in range(num_machines):
            m_type = random.choice(machine_types)
            year = random.randint(2018, 2024)
            code = f"M-{chc.id}-{i+100}"
            
            machine, created = Machine.objects.get_or_create(
                machine_code=code,
                defaults={
                    "machine_name": f"{m_type} {random.choice(['X1', 'Pro', 'Max', 'Eco'])}",
                    "machine_type": m_type,
                    "purchase_year": year,
                    "funding_source": random.choice(['SMAM', 'CRM', 'Self']),
                    "chc": chc,
                    "status": random.choice(statuses)
                }
            )
            created_machines.append(machine)
    return created_machines

def create_bookings_and_usage(machines):
    created_bookings = []
    
    for machine in machines:
        # Create 2-4 bookings per machine
        for _ in range(random.randint(2, 4)):
            # Random date within last 30 days to next 10 days
            delta = random.randint(-30, 10)
            start_date = date.today() + timedelta(days=delta)
            end_date = start_date + timedelta(days=random.randint(1, 3))
            
            status = 'Pending'
            if end_date < date.today():
                status = 'Completed'
            elif start_date <= date.today() <= end_date:
                status = 'Active'
                # Ensure machine status matches
                machine.status = 'In Use'
                machine.save()

            farmer_name = fake.name()
            
            booking, created = Booking.objects.get_or_create(
                machine=machine,
                start_date=start_date,
                defaults={
                    "end_date": end_date,
                    "chc": machine.chc,
                    "farmer_name": farmer_name,
                    "farmer_contact": f"9{fake.msisdn()[1:10]}",
                    "farmer_email": f"farmer.{random.randint(1000,9999)}@example.com",
                    "farmer_aadhar": str(fake.random_number(digits=12)),
                    "status": status,
                    "field_area": round(random.uniform(2.0, 15.0), 1),
                    "purpose": "Crop Residue Management"
                }
            )
            created_bookings.append(booking)

            # Create Usage if Completed
            if status == 'Completed' and created:
                MachineUsage.objects.create(
                     machine=machine,
                     booking=booking,
                     chc=machine.chc,
                     farmer_name=farmer_name,
                     usage_date=end_date,
                     start_time=datetime.strptime("09:00", "%H:%M").time(),
                     end_time=datetime.strptime("17:00", "%H:%M").time(),
                     total_hours_used=8,
                     residue_managed=round(random.uniform(5.0, 20.0), 1),
                     area_covered=booking.field_area,
                     fuel_consumed=round(random.uniform(10.0, 50.0), 1)
                )

    return created_bookings

def export_data_to_json():
    # Gather data
    data = {
        "generated_at": str(datetime.now()),
        "users": list(User.objects.values('username', 'role', 'email')),
        "chcs": list(CHC.objects.values('chc_name', 'district')),
        "machines": list(Machine.objects.values('machine_code', 'machine_name', 'status', 'chc__chc_name')),
        "bookings_count": Booking.objects.count(),
        "usage_records_count": MachineUsage.objects.count()
    }
    
    with open('populated_data.json', 'w') as f:
        json.dump(data, f, indent=4)
    
    print(f"Data exported to populated_data.json")

def main():
    print("Starting Realistic Data Population...")
    users = create_users()
    chcs = create_chcs()
    print(f"Created/Checked {len(chcs)} CHCs")
    
    machines = create_machines(chcs)
    print(f"Created/Checked {len(machines)} Machines")
    
    bookings = create_bookings_and_usage(machines)
    print(f"Created/Checked {len(bookings)} Bookings and Usage records")
    
    export_data_to_json()
    print("Population Complete!")

if __name__ == '__main__':
    main()

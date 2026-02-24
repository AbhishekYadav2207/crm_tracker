import random
from datetime import datetime, timedelta, date
from decimal import Decimal
import logging
from collections import defaultdict

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db import models, transaction
from django.db.models import Q
from faker import Faker

from accounts.models import User
from chc.models import CHC
from machines.models import Machine
from bookings.models import Booking
from usage.models import MachineUsage
from analytics.models import AuditLog, Notification

logger = logging.getLogger(__name__)

class DataGenerator:
    def __init__(self, locale='en_IN'):
        self.fake = Faker(locale)
        self.used_emails = set()
        self.used_usernames = set()
        self.used_phones = set()
        self.used_aadhaars = set()
        self.used_machine_codes = set()

    def unique_email(self, prefix, domain='example.com'):
        email = f"{prefix.lower().replace(' ', '.')}.{random.randint(1000,9999)}@{domain}"
        while email in self.used_emails:
            email = f"{prefix.lower()}.{random.randint(1000,9999)}@{domain}"
        self.used_emails.add(email)
        return email

    def unique_username(self, role, location):
        if role == 'GOVT_ADMIN':
            base = f"gov_{location[:3].lower()}_{random.randint(10,99)}"
        else:  # CHC_ADMIN
            base = f"adm_{location[:3].lower()}_{random.randint(10,99)}"
        username = base
        c = 1
        while username in self.used_usernames:
            username = f"{base[:8]}{c}"
            c += 1
        self.used_usernames.add(username)
        return username

    def unique_phone(self):
        phone = self.fake.msisdn()[:10]
        while phone in self.used_phones or not phone[0] in '6789':
            phone = self.fake.msisdn()[:10]
        self.used_phones.add(phone)
        return phone

    def unique_aadhaar(self):
        a = ''.join(str(random.randint(0,9)) for _ in range(12))
        while a in self.used_aadhaars:
            a = ''.join(str(random.randint(0,9)) for _ in range(12))
        self.used_aadhaars.add(a)
        return a

    def unique_machine_code(self, chc_id, mtype):
        code = f"{mtype[:3].upper()}{chc_id}{random.randint(1000,9999)}"
        while code in self.used_machine_codes:
            code = f"{mtype[:3].upper()}{chc_id}{random.randint(1000,9999)}"
        self.used_machine_codes.add(code)
        return code


class Command(BaseCommand):
    help = 'Populate DB with completed bookings + 3 pending & 3 active per CHC'

    def add_arguments(self, parser):
        parser.add_argument('--clear', action='store_true')
        parser.add_argument('--chcs', type=int, default=15)
        parser.add_argument('--machines-per-chc', type=int, default=20)
        parser.add_argument('--completed-per-machine', type=int, default=10)
        parser.add_argument('--seed', type=int, default=42)

    def handle(self, *args, **options):
        random.seed(options['seed'])
        Faker.seed(options['seed'])
        self.gen = DataGenerator()
        self.config = options
        self.data = {'chcs': [], 'users': [], 'machines': [], 'bookings': [], 'usages': []}

        self.stdout.write(self.style.WARNING("Starting population..."))

        if options['clear']:
            self.clear_data()

        with transaction.atomic():
            self.create_chcs()
            self.create_chc_admins()
            self.create_govt_admins()
            self.create_machines()
            self.create_bookings_and_usage()
            self.update_machine_status()
            self.create_audit_logs()
            self.create_notifications()
            self.validate_data()

        self.print_summary()
        self.stdout.write(self.style.SUCCESS("Done!"))

    def clear_data(self):
        self.stdout.write("Clearing existing data...")
        for model in [Notification, AuditLog, MachineUsage, Booking, Machine, User, CHC]:
            model.objects.all().delete()
        self.stdout.write(self.style.SUCCESS("Cleared."))

    def create_chcs(self):
        states = {
            'Punjab': ['Ludhiana','Amritsar','Jalandhar','Patiala','Bathinda'],
            'Haryana': ['Karnal','Hisar','Rohtak','Ambala','Gurugram'],
            'UP': ['Agra','Lucknow','Varanasi','Meerut','Kanpur'],
            'Rajasthan': ['Jaipur','Jodhpur','Kota','Bikaner','Ajmer'],
            'MP': ['Bhopal','Indore','Gwalior','Jabalpur','Ujjain'],
        }
        coords = {'Punjab':(30.9,75.8), 'Haryana':(29.1,76.0), 'UP':(27.6,80.0),
                  'Rajasthan':(26.9,75.8), 'MP':(23.5,77.0)}
        for _ in range(self.config['chcs']):
            state = random.choice(list(states.keys()))
            district = random.choice(states[state])
            name = f"{district} {random.choice(['CHC','Farm Machinery Bank','Kisan Sewa Kendra'])}"
            lat, lon = coords.get(state, (28.6,77.2))
            lat += random.uniform(-1,1)
            lon += random.uniform(-1,1)
            chc = CHC.objects.create(
                chc_name=name,
                state=state,
                district=district,
                location=self.gen.fake.street_address(),
                pincode=self.gen.fake.postcode()[:6],
                contact_number=self.gen.unique_phone(),
                email=self.gen.unique_email(f"chc{district[:3]}"),
                total_machines=0,
                is_active=True,
                registration_date=self.gen.fake.date_time_between(start_date='-4y', end_date='-1M'),
                latitude=Decimal(str(lat)).quantize(Decimal('0.000001')),
                longitude=Decimal(str(lon)).quantize(Decimal('0.000001')),
            )
            self.data['chcs'].append(chc)
        self.stdout.write(self.style.SUCCESS(f"Created {len(self.data['chcs'])} CHCs"))

    def create_chc_admins(self):
        for chc in self.data['chcs']:
            loc = chc.district[:3]
            user = User.objects.create_user(
                username=self.gen.unique_username('CHC_ADMIN', loc),
                email=self.gen.unique_email(f"adm.{loc}"),
                password='Chc@123456',
                role='CHC_ADMIN',
                chc=chc,
                phone_no=self.gen.unique_phone(),
                designation='CHC Manager',
                first_name=self.gen.fake.first_name(),
                last_name=self.gen.fake.last_name(),
                is_active=True
            )
            self.data['users'].append(user)
        self.stdout.write(self.style.SUCCESS(f"Created {len([u for u in self.data['users'] if u.role=='CHC_ADMIN'])} CHC admins"))

    def create_govt_admins(self):
        locs = ['DEL','LKO','CHD','BPL','JPR']
        for loc in locs:
            user = User.objects.create_user(
                username=self.gen.unique_username('GOVT_ADMIN', loc),
                email=self.gen.unique_email(f"govt.{loc.lower()}", 'gov.in'),
                password='Govt@123456',
                role='GOVT_ADMIN',
                phone_no=self.gen.unique_phone(),
                designation=random.choice(['State Agriculture Officer','District Agriculture Officer','Program Coordinator']),
                first_name=self.gen.fake.first_name(),
                last_name=self.gen.fake.last_name(),
                is_staff=True,
                is_active=True
            )
            self.data['users'].append(user)
        self.stdout.write(self.style.SUCCESS(f"Created {len([u for u in self.data['users'] if u.role=='GOVT_ADMIN'])} govt admins"))

    def create_machines(self):
        machine_types = {
            'Happy Seeder': {'hp':(45,75)},
            'Super Seeder': {'hp':(50,85)},
            'Smart Seeder': {'hp':(40,70)},
            'Mulcher': {'hp':(40,65)},
            'Rotavator': {'hp':(35,60)},
            'Zero Tillage Drill': {'hp':(35,55)},
            'Laser Land Leveller': {'hp':(60,100)},
            'Straw Baler': {'hp':(50,90)},
        }
        # Initially all machines Idle (except those that may become In Use later)
        for chc in self.data['chcs']:
            num = random.randint(int(self.config['machines_per_chc']*0.8), int(self.config['machines_per_chc']*1.2))
            for _ in range(num):
                mtype = random.choice(list(machine_types.keys()))
                code = self.gen.unique_machine_code(chc.id, mtype)
                purchase_year = random.choices(range(2019,2025), weights=[0.05,0.1,0.15,0.25,0.3,0.15])[0]
                today = date.today()
                last_serviced = self.gen.fake.date_between(start_date='-1y', end_date='-1M')
                interval = random.randint(180,365)
                next_service = last_serviced + timedelta(days=interval)
                if next_service < today:
                    next_service = today + timedelta(days=random.randint(1,30))
                machine = Machine.objects.create(
                    machine_code=code,
                    chc=chc,
                    machine_name=f"{mtype} {random.choice(['Pro','Plus','Deluxe'])}",
                    machine_type=mtype,
                    purchase_year=purchase_year,
                    funding_source=random.choice(['SMAM','RKVY','NABARD',None]),
                    status='Idle',  # start idle
                    total_hours_used=0,
                    last_serviced_date=last_serviced,
                    next_service_due=next_service,
                )
                self.data['machines'].append(machine)
            chc.total_machines = Machine.objects.filter(chc=chc).count()
            chc.save()
        self.stdout.write(self.style.SUCCESS(f"Created {len(self.data['machines'])} machines"))

    def create_bookings_and_usage(self):
        # Farmer data pools
        first_names = ['Ram','Shyam','Hari','Mohan','Sohan','Ramesh','Suresh','Dinesh','Mahesh','Gopal']
        last_names = ['Singh','Kumar','Sharma','Verma','Yadav','Patel','Gupta','Reddy','Nair']
        villages = ['Rampur','Nagla','Shahpur','Sultanpur','Raipur','Gopalpur','Kishanpur','Malikpur','Bassi','Dhani']
        crops = ['Wheat','Paddy','Sugarcane','Maize','Cotton','Mustard','Bajra','Gram']
        seasons = ['Rabi','Kharif','Zaid']

        today = date.today()

        # Track counts per CHC for pending and active
        pending_needed = {chc.id: 3 for chc in self.data['chcs']}
        active_needed = {chc.id: 3 for chc in self.data['chcs']}

        total_completed = 0
        total_pending = 0
        total_active = 0
        total_usages = 0

        for machine in self.data['machines']:
            chc_id = machine.chc.id

            # --- Create completed bookings (past) ---
            num_completed = random.randint(
                int(self.config['completed_per_machine']*0.8),
                int(self.config['completed_per_machine']*1.2)
            )
            for _ in range(num_completed):
                # Random past date up to 180 days ago, but ensure end_date is before today
                max_past = today - timedelta(days=1)
                min_past = today - timedelta(days=180)
                start_date = self.gen.fake.date_between(start_date=min_past, end_date=max_past)
                # Duration
                if 'Seeder' in machine.machine_type or 'Drill' in machine.machine_type:
                    duration = random.randint(3,6)
                elif 'Leveller' in machine.machine_type:
                    duration = random.randint(2,5)
                elif 'Baler' in machine.machine_type:
                    duration = random.randint(4,8)
                else:
                    duration = random.randint(2,7)
                end_date = start_date + timedelta(days=duration)
                if end_date >= today:
                    end_date = today - timedelta(days=1)  # ensure completed

                farmer = {
                    'name': f"{random.choice(first_names)} {random.choice(last_names)}",
                    'phone': self.gen.unique_phone(),
                    'email': self.gen.unique_email('farmer'),
                    'aadhaar': self.gen.unique_aadhaar(),
                }
                crop = random.choice(crops)
                village = random.choice(villages)
                season = random.choice(seasons)
                purpose = f"{crop} cultivation - {village} ({season})"
                field_area = Decimal(str(random.uniform(1.0,25.0))).quantize(Decimal('0.01'))

                booking_date = self.gen.fake.date_time_between(
                    start_date=start_date - timedelta(days=20),
                    end_date=start_date
                )

                booking = Booking.objects.create(
                    chc=machine.chc,
                    machine=machine,
                    start_date=start_date,
                    end_date=end_date,
                    status='Completed',
                    farmer_name=farmer['name'],
                    farmer_contact=farmer['phone'],
                    farmer_email=farmer['email'],
                    farmer_aadhar=farmer['aadhaar'],
                    field_area=field_area,
                    purpose=purpose,
                    booking_date=booking_date,
                )
                self.data['bookings'].append(booking)
                total_completed += 1

                # Create usage records for this completed booking
                usages = self.create_usage_for_booking(booking, farmer)
                total_usages += len(usages)
                self.data['usages'].extend(usages)

            # --- Add pending bookings if still needed for this CHC ---
            if pending_needed[chc_id] > 0:
                # Create a pending booking (future)
                # We'll create up to needed, but we can spread across machines
                # For simplicity, we'll create one per machine until quota filled
                if pending_needed[chc_id] > 0:
                    # Future start date between tomorrow and +90 days
                    start_date = self.gen.fake.date_between(start_date=today + timedelta(days=1), end_date=today + timedelta(days=90))
                    duration = random.randint(3,7)
                    end_date = start_date + timedelta(days=duration)

                    farmer = {
                        'name': f"{random.choice(first_names)} {random.choice(last_names)}",
                        'phone': self.gen.unique_phone(),
                        'email': self.gen.unique_email('farmer'),
                        'aadhaar': self.gen.unique_aadhaar(),
                    }
                    crop = random.choice(crops)
                    village = random.choice(villages)
                    season = random.choice(seasons)
                    purpose = f"{crop} cultivation - {village} ({season})"
                    field_area = Decimal(str(random.uniform(1.0,25.0))).quantize(Decimal('0.01'))

                    booking_date = self.gen.fake.date_time_between(
                        start_date=start_date - timedelta(days=30),
                        end_date=start_date - timedelta(days=1)
                    )

                    booking = Booking.objects.create(
                        chc=machine.chc,
                        machine=machine,
                        start_date=start_date,
                        end_date=end_date,
                        status='Pending',  # or 'Approved'? We'll use 'Pending' for future not yet approved
                        farmer_name=farmer['name'],
                        farmer_contact=farmer['phone'],
                        farmer_email=farmer['email'],
                        farmer_aadhar=farmer['aadhaar'],
                        field_area=field_area,
                        purpose=purpose,
                        booking_date=booking_date,
                    )
                    self.data['bookings'].append(booking)
                    total_pending += 1
                    pending_needed[chc_id] -= 1

            # --- Add active bookings if still needed for this CHC ---
            if active_needed[chc_id] > 0:
                # Create an active booking (today's date within range)
                # Start date could be a few days ago, end date a few days ahead, so today is inside
                start_date = today - timedelta(days=random.randint(1,3))
                duration = random.randint(5,10)
                end_date = start_date + timedelta(days=duration)
                # Ensure end_date is after today
                if end_date <= today:
                    end_date = today + timedelta(days=random.randint(1,5))

                farmer = {
                    'name': f"{random.choice(first_names)} {random.choice(last_names)}",
                    'phone': self.gen.unique_phone(),
                    'email': self.gen.unique_email('farmer'),
                    'aadhaar': self.gen.unique_aadhaar(),
                }
                crop = random.choice(crops)
                village = random.choice(villages)
                season = random.choice(seasons)
                purpose = f"{crop} cultivation - {village} ({season})"
                field_area = Decimal(str(random.uniform(1.0,25.0))).quantize(Decimal('0.01'))

                booking_date = self.gen.fake.date_time_between(
                    start_date=start_date - timedelta(days=20),
                    end_date=start_date
                )

                booking = Booking.objects.create(
                    chc=machine.chc,
                    machine=machine,
                    start_date=start_date,
                    end_date=end_date,
                    status='Active',
                    farmer_name=farmer['name'],
                    farmer_contact=farmer['phone'],
                    farmer_email=farmer['email'],
                    farmer_aadhar=farmer['aadhaar'],
                    field_area=field_area,
                    purpose=purpose,
                    booking_date=booking_date,
                )
                self.data['bookings'].append(booking)
                total_active += 1
                active_needed[chc_id] -= 1

        # After all machines, if any pending/active still needed (shouldn't happen if enough machines)
        # But just in case, we can add them to random machines of that CHC
        for chc in self.data['chcs']:
            while pending_needed[chc.id] > 0:
                machine = random.choice([m for m in self.data['machines'] if m.chc.id == chc.id])
                # create pending as above...
                # (similar code, we can duplicate or call a helper)
                start_date = self.gen.fake.date_between(start_date=today + timedelta(days=1), end_date=today + timedelta(days=90))
                duration = random.randint(3,7)
                end_date = start_date + timedelta(days=duration)
                farmer = {
                    'name': f"{random.choice(first_names)} {random.choice(last_names)}",
                    'phone': self.gen.unique_phone(),
                    'email': self.gen.unique_email('farmer'),
                    'aadhaar': self.gen.unique_aadhaar(),
                }
                crop = random.choice(crops)
                village = random.choice(villages)
                season = random.choice(seasons)
                purpose = f"{crop} cultivation - {village} ({season})"
                field_area = Decimal(str(random.uniform(1.0,25.0))).quantize(Decimal('0.01'))
                booking_date = self.gen.fake.date_time_between(
                    start_date=start_date - timedelta(days=30),
                    end_date=start_date - timedelta(days=1)
                )
                booking = Booking.objects.create(
                    chc=machine.chc,
                    machine=machine,
                    start_date=start_date,
                    end_date=end_date,
                    status='Pending',
                    farmer_name=farmer['name'],
                    farmer_contact=farmer['phone'],
                    farmer_email=farmer['email'],
                    farmer_aadhar=farmer['aadhaar'],
                    field_area=field_area,
                    purpose=purpose,
                    booking_date=booking_date,
                )
                self.data['bookings'].append(booking)
                total_pending += 1
                pending_needed[chc.id] -= 1

            while active_needed[chc.id] > 0:
                machine = random.choice([m for m in self.data['machines'] if m.chc.id == chc.id])
                start_date = today - timedelta(days=random.randint(1,3))
                duration = random.randint(5,10)
                end_date = start_date + timedelta(days=duration)
                if end_date <= today:
                    end_date = today + timedelta(days=random.randint(1,5))
                farmer = {
                    'name': f"{random.choice(first_names)} {random.choice(last_names)}",
                    'phone': self.gen.unique_phone(),
                    'email': self.gen.unique_email('farmer'),
                    'aadhaar': self.gen.unique_aadhaar(),
                }
                crop = random.choice(crops)
                village = random.choice(villages)
                season = random.choice(seasons)
                purpose = f"{crop} cultivation - {village} ({season})"
                field_area = Decimal(str(random.uniform(1.0,25.0))).quantize(Decimal('0.01'))
                booking_date = self.gen.fake.date_time_between(
                    start_date=start_date - timedelta(days=20),
                    end_date=start_date
                )
                booking = Booking.objects.create(
                    chc=machine.chc,
                    machine=machine,
                    start_date=start_date,
                    end_date=end_date,
                    status='Active',
                    farmer_name=farmer['name'],
                    farmer_contact=farmer['phone'],
                    farmer_email=farmer['email'],
                    farmer_aadhar=farmer['aadhaar'],
                    field_area=field_area,
                    purpose=purpose,
                    booking_date=booking_date,
                )
                self.data['bookings'].append(booking)
                total_active += 1
                active_needed[chc.id] -= 1

        self.stdout.write(self.style.SUCCESS(f"Created {total_completed} completed, {total_pending} pending, {total_active} active bookings"))
        self.stdout.write(self.style.SUCCESS(f"Created {total_usages} usage records (only for completed)"))

    def create_usage_for_booking(self, booking, farmer):
        usages = []
        days = (booking.end_date - booking.start_date).days
        if days <= 0:
            return usages

        # Determine number of usage sessions
        if days <= 2:
            sessions = 1
        elif days <= 5:
            sessions = random.randint(1,2)
        else:
            sessions = random.randint(2,4)

        # Distribute session dates
        session_dates = []
        for i in range(sessions):
            if sessions == 1:
                d = booking.start_date + timedelta(days=days//2)
            else:
                offset = (i * days) // (sessions - 1) if sessions > 1 else 0
                d = booking.start_date + timedelta(days=offset)
            if d < booking.start_date:
                d = booking.start_date
            if d > booking.end_date:
                d = booking.end_date
            session_dates.append(d)

        total_area = float(booking.field_area)
        remaining = total_area
        operators = ['Raj Kumar','Sukhwinder Singh','Gurpreet Singh','Mohan Lal','Ramesh Kumar']

        for i, sdate in enumerate(session_dates):
            if i == len(session_dates)-1:
                area = remaining
            else:
                area = remaining * random.uniform(0.2, 0.5)
                remaining -= area
            area = Decimal(str(round(area,2)))

            # Hours estimation
            if 'Seeder' in booking.machine.machine_type:
                hrs_needed = float(area) * random.uniform(0.8,1.2)
            elif 'Leveller' in booking.machine.machine_type:
                hrs_needed = float(area) * random.uniform(0.6,1.0)
            else:
                hrs_needed = float(area) * random.uniform(0.7,1.3)
            hrs = min(int(hrs_needed), 12)
            start_hour = random.randint(6,8)
            end_hour = min(start_hour + hrs, 19)
            start_time = datetime.strptime(f"{start_hour}:00","%H:%M").time()
            end_time = datetime.strptime(f"{end_hour}:00","%H:%M").time()

            # Residue
            if 'Baler' in booking.machine.machine_type:
                residue_rate = Decimal(str(random.uniform(1.5,2.5)))
            elif 'Seeder' in booking.machine.machine_type:
                residue_rate = Decimal(str(random.uniform(0.4,0.7)))
            else:
                residue_rate = Decimal(str(random.uniform(0.3,0.8)))
            residue = (area * residue_rate).quantize(Decimal('0.01'))

            # Fuel
            if 'Happy Seeder' in booking.machine.machine_type or 'Super Seeder' in booking.machine.machine_type:
                fuel_rate = Decimal(str(random.uniform(4.0,6.0)))
            else:
                fuel_rate = Decimal(str(random.uniform(2.5,4.5)))
            fuel = (Decimal(str(hrs)) * fuel_rate).quantize(Decimal('0.1'))

            # Meter
            base = random.randint(1000,50000) + i*100
            start_meter = Decimal(str(base)).quantize(Decimal('0.1'))
            end_meter = (start_meter + Decimal(str(hrs * random.uniform(0.9,1.1)))).quantize(Decimal('0.1'))

            usage = MachineUsage(
                machine=booking.machine,
                chc=booking.chc,
                booking=booking,
                farmer_name=farmer['name'],
                farmer_contact=farmer['phone'],
                farmer_aadhar=farmer['aadhaar'],
                usage_date=sdate,
                start_time=start_time,
                end_time=end_time,
                total_hours_used=Decimal(str(hrs)),
                start_meter_reading=start_meter,
                end_meter_reading=end_meter,
                gps_lat=booking.chc.latitude + Decimal(str(random.uniform(-0.02,0.02))).quantize(Decimal('0.000001')),
                gps_lng=booking.chc.longitude + Decimal(str(random.uniform(-0.02,0.02))).quantize(Decimal('0.000001')),
                purpose=f"Session {i+1}: {booking.purpose}",
                crop_type=booking.purpose.split()[0],
                area_covered=area,
                residue_managed=residue,
                fuel_consumed=fuel,
                operator_name=random.choice(operators),
                remarks=f"Session {i+1} completed" if random.random()>0.2 else f"Minor issues in session {i+1}",
            )
            usages.append(usage)

        if usages:
            MachineUsage.objects.bulk_create(usages)

        # Update machine total hours (only from completed usages)
        total = MachineUsage.objects.filter(machine=booking.machine).aggregate(total=models.Sum('total_hours_used'))['total'] or 0
        booking.machine.total_hours_used = total
        booking.machine.save()

        return usages

    def update_machine_status(self):
        """Set machine status to 'In Use' if there's an active booking today."""
        today = date.today()
        for machine in self.data['machines']:
            active = Booking.objects.filter(
                machine=machine,
                start_date__lte=today,
                end_date__gte=today,
                status='Active'
            ).exists()
            if active:
                machine.status = 'In Use'
            else:
                # Keep as Idle (or could be Maintenance if needed)
                if machine.status != 'Maintenance' and machine.status != 'Out of Service':
                    machine.status = 'Idle'
            machine.save()
        self.stdout.write(self.style.SUCCESS("Updated machine statuses based on active bookings"))

    def create_audit_logs(self):
        # Simplified: create some logs for machines and bookings
        users = list(User.objects.all())
        logs = []
        for machine in random.sample(self.data['machines'], min(50, len(self.data['machines']))):
            logs.append(AuditLog(
                user=random.choice(users) if users else None,
                action_type='CREATE',
                table_name='machines_machine',
                record_id=str(machine.id),
                new_value={'code': machine.machine_code},
                timestamp=timezone.make_aware(self.gen.fake.date_time_between(start_date='-1y', end_date='now'))
            ))
        for booking in random.sample(self.data['bookings'], min(100, len(self.data['bookings']))):
            if booking.status in ['Approved','Rejected','Completed']:
                logs.append(AuditLog(
                    user=User.objects.filter(chc=booking.chc, role='CHC_ADMIN').first(),
                    action_type=booking.status.upper(),
                    table_name='bookings_booking',
                    record_id=str(booking.id),
                    new_value={'status': booking.status},
                    timestamp=timezone.make_aware(self.gen.fake.date_time_between(start_date=booking.booking_date, end_date=booking.updated_at))
                ))
        if logs:
            AuditLog.objects.bulk_create(logs)
        self.stdout.write(self.style.SUCCESS(f"Created {AuditLog.objects.count()} audit logs"))

    def create_notifications(self):
        users = User.objects.filter(role__in=['CHC_ADMIN','GOVT_ADMIN'])
        notifs = []
        for user in users:
            for _ in range(random.randint(20,40)):
                notifs.append(Notification(
                    user=user,
                    title=random.choice(['New Booking','Machine Due','Report Ready']),
                    message=self.gen.fake.sentence(),
                    notification_type=random.choice(['BOOKING','MAINTENANCE','REPORT']),
                    is_read=random.random()<0.3,
                    created_at=timezone.make_aware(self.gen.fake.date_time_between(start_date='-1M', end_date='now'))
                ))
        if notifs:
            Notification.objects.bulk_create(notifs)
        self.stdout.write(self.style.SUCCESS(f"Created {Notification.objects.count()} notifications"))

    def validate_data(self):
        issues = []
        today = date.today()
        # Check each machine with active booking has status 'In Use'
        for machine in self.data['machines']:
            has_active = Booking.objects.filter(machine=machine, start_date__lte=today, end_date__gte=today, status='Active').exists()
            if has_active and machine.status != 'In Use':
                issues.append(f"Machine {machine.id} has active booking but status {machine.status}")
            if not has_active and machine.status == 'In Use':
                issues.append(f"Machine {machine.id} is In Use but no active booking")
        # Check pending and active counts per CHC
        for chc in self.data['chcs']:
            pending_count = Booking.objects.filter(chc=chc, status='Pending').count()
            active_count = Booking.objects.filter(chc=chc, status='Active').count()
            if pending_count != 3:
                issues.append(f"CHC {chc.id} has {pending_count} pending, expected 3")
            if active_count != 3:
                issues.append(f"CHC {chc.id} has {active_count} active, expected 3")
        if issues:
            self.stdout.write(self.style.WARNING(f"Validation found {len(issues)} issues"))
            for iss in issues[:5]:
                self.stdout.write(f"  - {iss}")
        else:
            self.stdout.write(self.style.SUCCESS("All validations passed"))

    def print_summary(self):
        self.stdout.write(self.style.SUCCESS("\n" + "="*60))
        self.stdout.write("SUMMARY")
        self.stdout.write(f"CHCs: {len(self.data['chcs'])}")
        self.stdout.write(f"Users: {len(self.data['users'])} (CHC Admins: {len([u for u in self.data['users'] if u.role=='CHC_ADMIN'])}, Govt: {len([u for u in self.data['users'] if u.role=='GOVT_ADMIN'])})")
        self.stdout.write(f"Machines: {len(self.data['machines'])}")
        self.stdout.write(f"Bookings: {len(self.data['bookings'])}")
        completed = Booking.objects.filter(status='Completed').count()
        pending = Booking.objects.filter(status='Pending').count()
        active = Booking.objects.filter(status='Active').count()
        self.stdout.write(f"  - Completed: {completed}")
        self.stdout.write(f"  - Pending: {pending}")
        self.stdout.write(f"  - Active: {active}")
        self.stdout.write(f"Usage records: {len(self.data['usages'])}")
        in_use_count = Machine.objects.filter(status='In Use').count()
        self.stdout.write(f"Machines in use: {in_use_count}")
        self.stdout.write("="*60)
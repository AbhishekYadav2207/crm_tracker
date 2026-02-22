import random
import uuid
from datetime import datetime, timedelta, date
from decimal import Decimal
import hashlib
from typing import List, Dict, Any, Optional
import logging

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db import models, transaction
from django.db.utils import IntegrityError
from faker import Faker

# Import your models - adjust these imports to match your app structure
from accounts.models import User
from chc.models import CHC
from machines.models import Machine
from bookings.models import Booking
from usage.models import MachineUsage
from analytics.models import AuditLog, Notification

# Set up logging
logger = logging.getLogger(__name__)

class DataGenerator:
    """Helper class to generate unique data across the application."""
    
    def __init__(self, locale='en_IN'):
        self.fake = Faker(locale)
        self.used_emails = set()
        self.used_usernames = set()
        self.used_phone_numbers = set()
        self.used_aadhaars = set()
        self.used_machine_codes = set()
        
    def generate_unique_email(self, base: str = None, domain: str = 'example.com') -> str:
        """Generate a unique email address."""
        if not base:
            base = self.fake.user_name()
        
        # Clean base and ensure it's valid
        base = base.lower().replace(' ', '.').replace('_', '.').replace('-', '.')
        base = ''.join(c for c in base if c.isalnum() or c == '.')
        
        # Add timestamp and random suffix for uniqueness
        timestamp = datetime.now().strftime('%H%M%S')
        random_suffix = random.randint(100, 999)
        email = f"{base}.{timestamp}.{random_suffix}@{domain}"
        
        # Ensure uniqueness
        while email in self.used_emails:
            random_suffix = random.randint(100, 999)
            email = f"{base}.{timestamp}.{random_suffix}@{domain}"
        
        self.used_emails.add(email)
        return email
    
    def generate_unique_username(self, base: str) -> str:
        """Generate a unique username."""
        username = base.lower().replace(' ', '_').replace('.', '_')
        username = ''.join(c for c in username if c.isalnum() or c == '_')
        
        # Add random suffix for uniqueness
        random_suffix = random.randint(1000, 9999)
        final_username = f"{username}_{random_suffix}"
        
        while final_username in self.used_usernames:
            random_suffix = random.randint(1000, 9999)
            final_username = f"{username}_{random_suffix}"
        
        self.used_usernames.add(final_username)
        return final_username
    
    def generate_unique_phone(self) -> str:
        """Generate a unique 10-digit phone number."""
        max_attempts = 100
        for _ in range(max_attempts):
            phone = self.fake.msisdn()[:10]
            if phone not in self.used_phone_numbers and len(phone) == 10:
                self.used_phone_numbers.add(phone)
                return phone
        
        # Fallback: generate random 10-digit number
        phone = f"9{random.randint(100000000, 999999999)}"
        while phone in self.used_phone_numbers:
            phone = f"9{random.randint(100000000, 999999999)}"
        self.used_phone_numbers.add(phone)
        return phone
    
    def generate_unique_aadhaar(self) -> str:
        """Generate a unique 12-digit Aadhaar number."""
        max_attempts = 100
        for _ in range(max_attempts):
            aadhaar = self.fake.aadhaar_id()
            if aadhaar not in self.used_aadhaars and len(aadhaar) == 12:
                self.used_aadhaars.add(aadhaar)
                return aadhaar
        
        # Fallback: generate random 12-digit number with checksum
        aadhaar = ''.join([str(random.randint(0, 9)) for _ in range(12)])
        while aadhaar in self.used_aadhaars:
            aadhaar = ''.join([str(random.randint(0, 9)) for _ in range(12)])
        self.used_aadhaars.add(aadhaar)
        return aadhaar
    
    def generate_unique_machine_code(self, chc_id: int, machine_type: str) -> str:
        """Generate a unique machine code."""
        type_code = machine_type[:3].upper()
        timestamp = datetime.now().strftime('%H%M')
        random_part = random.randint(100, 999)
        machine_code = f"CHC{chc_id}-{type_code}-{timestamp}-{random_part}"
        
        while machine_code in self.used_machine_codes:
            random_part = random.randint(100, 999)
            machine_code = f"CHC{chc_id}-{type_code}-{timestamp}-{random_part}"
        
        self.used_machine_codes.add(machine_code)
        return machine_code


class ProgressTracker:
    """Track progress of data creation."""
    
    def __init__(self, total_steps: int, command):
        self.total_steps = total_steps
        self.current_step = 0
        self.command = command
        self.start_time = datetime.now()
        
    def update(self, message: str, step_increment: int = 1):
        """Update progress."""
        self.current_step += step_increment
        elapsed = (datetime.now() - self.start_time).total_seconds()
        percentage = (self.current_step / self.total_steps) * 100
        
        self.command.stdout.write(f"[{percentage:3.1f}%] {message}")
        
    def complete(self):
        """Mark progress as complete."""
        elapsed = (datetime.now() - self.start_time).total_seconds()
        self.command.stdout.write(self.command.style.SUCCESS(f"✓ Completed in {elapsed:.1f} seconds"))


class Command(BaseCommand):
    help = 'Advanced database population with realistic, connected test data'
    
    def add_arguments(self, parser):
        parser.add_argument('--clear', action='store_true', help='Delete existing data before populating')
        parser.add_argument('--chcs', type=int, default=10, help='Number of CHCs to create (default: 10)')
        parser.add_argument('--machines-per-chc', type=int, default=15, help='Average machines per CHC (default: 15)')
        parser.add_argument('--bookings-per-machine', type=int, default=8, help='Average bookings per machine (default: 8)')
        parser.add_argument('--seed', type=int, help='Random seed for reproducible data')
        parser.add_argument('--verbose', action='store_true', help='Verbose output')
        
    def handle(self, *args, **options):
        # Set random seed if provided
        if options['seed']:
            random.seed(options['seed'])
            self.stdout.write(f"Using random seed: {options['seed']}")
        
        # Initialize generator
        self.gen = DataGenerator()
        
        # Store configuration
        self.config = {
            'num_chcs': options['chcs'],
            'machines_per_chc': options['machines_per_chc'],
            'bookings_per_machine': options['bookings_per_machine'],
            'verbose': options['verbose'],
        }
        
        # Initialize data storage
        self.data = {
            'chcs': [],
            'users': [],
            'machines': [],
            'bookings': [],
            'usages': [],
        }
        
        # Calculate total steps for progress tracking
        total_steps = 8  # Main steps
        self.progress = ProgressTracker(total_steps, self)
        
        self.stdout.write(self.style.WARNING("=" * 60))
        self.stdout.write(self.style.WARNING("STARTING DATABASE POPULATION"))
        self.stdout.write(self.style.WARNING(f"Configuration: {self.config}"))
        self.stdout.write(self.style.WARNING("=" * 60))
        
        try:
            if options['clear']:
                self.clear_data()
            
            with transaction.atomic():  # Wrap everything in a transaction
                self.progress.update("Creating CHCs...")
                self.create_chcs()
                
                self.progress.update("Creating users...")
                self.create_users()
                
                self.progress.update("Creating machines...")
                self.create_machines()
                
                self.progress.update("Creating bookings...")
                self.create_bookings()
                
                self.progress.update("Creating usage records...")
                self.create_usage_records()
                
                self.progress.update("Creating audit logs...")
                self.create_audit_logs()
                
                self.progress.update("Creating notifications...")
                self.create_notifications()
                
                self.progress.update("Validating data integrity...")
                self.validate_data()
            
            self.print_summary()
            self.stdout.write(self.style.SUCCESS("=" * 60))
            self.stdout.write(self.style.SUCCESS("DATABASE POPULATION COMPLETED SUCCESSFULLY"))
            self.stdout.write(self.style.SUCCESS("=" * 60))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error during population: {str(e)}"))
            if options['verbose']:
                import traceback
                self.stdout.write(traceback.format_exc())
            raise

    def clear_data(self):
        """Delete all data with proper cascade handling."""
        self.stdout.write("Clearing existing data...")
        
        # Delete in correct order to avoid foreign key constraints
        deletion_order = [
            ('Notifications', Notification),
            ('Audit Logs', AuditLog),
            ('Machine Usage', MachineUsage),
            ('Bookings', Booking),
            ('Machines', Machine),
            ('Users (non-superuser)', User.objects.filter(is_superuser=False)),
            ('CHCs', CHC),
        ]
        
        for name, model_or_queryset in deletion_order:
            try:
                if isinstance(model_or_queryset, type) and hasattr(model_or_queryset, 'objects'):
                    # It's a model class
                    count = model_or_queryset.objects.all().delete()[0]
                elif hasattr(model_or_queryset, 'delete'):
                    # It's a queryset
                    count = model_or_queryset.delete()[0]
                else:
                    count = 0
                
                self.stdout.write(f"  Deleted {count} {name}")
            except Exception as e:
                self.stdout.write(f"  Warning: Could not delete {name} - {str(e)}")
        
        self.stdout.write(self.style.SUCCESS("✓ Existing data cleared."))

    def create_chcs(self):
        """Create CHCs with realistic distribution."""
        states_districts = {
            'Punjab': ['Ludhiana', 'Amritsar', 'Jalandhar', 'Patiala', 'Bathinda', 'Ferozepur', 'Moga', 'Sangrur'],
            'Haryana': ['Karnal', 'Hisar', 'Rohtak', 'Ambala', 'Gurugram', 'Faridabad', 'Kurukshetra', 'Panipat'],
            'Uttar Pradesh': ['Agra', 'Lucknow', 'Varanasi', 'Meerut', 'Aligarh', 'Kanpur', 'Bareilly', 'Moradabad'],
            'Rajasthan': ['Jaipur', 'Jodhpur', 'Kota', 'Bikaner', 'Ajmer', 'Udaipur', 'Bhilwara', 'Alwar'],
            'Madhya Pradesh': ['Bhopal', 'Indore', 'Gwalior', 'Jabalpur', 'Ujjain', 'Sagar', 'Ratlam', 'Rewa'],
        }
        
        chc_suffixes = ['Custom Hiring Center', 'Farm Machinery Bank', 'Agri Service Center', 
                       'CHC', 'Farmers Service Center', 'Kisan Sewa Kendra']
        
        for i in range(self.config['num_chcs']):
            state = random.choice(list(states_districts.keys()))
            district = random.choice(states_districts[state])
            suffix = random.choice(chc_suffixes)
            
            # Vary CHC names
            name_variations = [
                f"{district} {suffix}",
                f"{self.gen.fake.city()} {suffix}",
                f"{district} Block {suffix}",
            ]
            chc_name = random.choice(name_variations)
            
            # Generate realistic coordinates for the region
            base_coords = {
                'Punjab': (30.9, 75.8),
                'Haryana': (29.1, 76.0),
                'Uttar Pradesh': (27.6, 80.0),
                'Rajasthan': (26.9, 75.8),
                'Madhya Pradesh': (23.5, 77.0),
            }
            
            base_lat, base_lon = base_coords.get(state, (28.6, 77.2))  # Default to Delhi region
            
            lat_variation = random.uniform(-1.5, 1.5)
            lon_variation = random.uniform(-1.5, 1.5)
            
            chc = CHC.objects.create(
                chc_name=chc_name,
                state=state,
                district=district,
                location=self.gen.fake.street_address(),
                pincode=self.gen.fake.postcode()[:6],
                contact_number=self.gen.generate_unique_phone(),
                email=self.gen.generate_unique_email(f"chc{district}"),
                total_machines=0,
                is_active=random.random() > 0.05,  # 95% active
                registration_date=self.gen.fake.date_time_between(start_date='-3y', end_date='-1M'),
                latitude=Decimal(str(base_lat + lat_variation)).quantize(Decimal('0.000001')),
                longitude=Decimal(str(base_lon + lon_variation)).quantize(Decimal('0.000001')),
            )
            self.data['chcs'].append(chc)
            
            if self.config['verbose']:
                self.stdout.write(f"    Created: {chc_name} in {district}, {state}")
        
        self.stdout.write(self.style.SUCCESS(f"  ✓ Created {len(self.data['chcs'])} CHCs"))

    def create_users(self):
        """Create users with realistic roles and relationships."""
        
        # Government admins
        govt_designations = [
            'State Agriculture Officer',
            'District Agriculture Officer',
            'Program Coordinator',
            'Scheme Administrator',
            'Monitoring Officer'
        ]
        
        for i in range(3):  # Create 3 government admins
            first_name = self.gen.fake.first_name()
            last_name = self.gen.fake.last_name()
            username = self.gen.generate_unique_username(f"govt_{first_name}_{last_name}")
            
            user = User.objects.create_user(
                username=username,
                email=self.gen.generate_unique_email(f"govt.{first_name}.{last_name}", 'gov.in'),
                password="Govt@123456",
                role='GOVT_ADMIN',
                phone_no=self.gen.generate_unique_phone(),
                designation=random.choice(govt_designations),
                first_name=first_name,
                last_name=last_name,
                is_staff=True,
            )
            self.data['users'].append(user)
        
        # CHC admins and staff
        chc_designations = {
            'CHC_ADMIN': ['CHC Manager', 'Center Coordinator', 'Operations Head', 'Farm Manager'],
            'CHC_STAFF': ['Field Assistant', 'Technician', 'Operator', 'Clerk', 'Accountant']
        }
        
        for chc in self.data['chcs']:
            # Create 1-2 admins per CHC
            num_admins = random.randint(1, 2)
            for j in range(num_admins):
                first_name = self.gen.fake.first_name()
                last_name = self.gen.fake.last_name()
                username = self.gen.generate_unique_username(f"admin_{chc.district}_{first_name}")
                
                admin = User.objects.create_user(
                    username=username,
                    email=self.gen.generate_unique_email(f"{chc.district}.chc.admin{j}"),
                    password="Chc@123456",
                    role='CHC_ADMIN',
                    chc=chc,
                    phone_no=self.gen.generate_unique_phone(),
                    designation=random.choice(chc_designations['CHC_ADMIN']),
                    first_name=first_name,
                    last_name=last_name
                )
                self.data['users'].append(admin)
            
            # Create 2-4 staff members per CHC
            num_staff = random.randint(2, 4)
            for j in range(num_staff):
                first_name = self.gen.fake.first_name()
                last_name = self.gen.fake.last_name()
                username = self.gen.generate_unique_username(f"staff_{chc.district}_{first_name}")
                
                staff = User.objects.create_user(
                    username=username,
                    email=self.gen.generate_unique_email(f"{chc.district}.staff{j}"),
                    password="Staff@123456",
                    role='CHC_ADMIN',  # Change this if you have other roles
                    chc=chc,
                    phone_no=self.gen.generate_unique_phone(),
                    designation=random.choice(chc_designations['CHC_STAFF']),
                    first_name=first_name,
                    last_name=last_name
                )
                self.data['users'].append(staff)
        
        self.stdout.write(self.style.SUCCESS(f"  ✓ Created {len(self.data['users'])} users"))

    def create_machines(self):
        """Create machines with realistic attributes and relationships."""
        
        # Enhanced machine types with specifications
        machine_specs = {
            'Happy Seeder': {'hp_range': (45, 75), 'price_range': (150000, 250000), 'weight': (400, 600)},
            'Super Seeder': {'hp_range': (50, 85), 'price_range': (180000, 300000), 'weight': (450, 700)},
            'Smart Seeder': {'hp_range': (40, 70), 'price_range': (200000, 350000), 'weight': (350, 550)},
            'Mulcher': {'hp_range': (40, 65), 'price_range': (120000, 200000), 'weight': (300, 500)},
            'Rotavator': {'hp_range': (35, 60), 'price_range': (80000, 150000), 'weight': (250, 450)},
            'Zero Tillage Drill': {'hp_range': (35, 55), 'price_range': (90000, 160000), 'weight': (300, 500)},
            'Straw Baler': {'hp_range': (50, 90), 'price_range': (300000, 500000), 'weight': (1000, 2000)},
            'Laser Land Leveller': {'hp_range': (60, 100), 'price_range': (400000, 700000), 'weight': (1500, 2500)},
        }
        
        # Add default specs for other types
        default_spec = {'hp_range': (30, 60), 'price_range': (50000, 200000), 'weight': (200, 800)}
        
        status_choices = ['Idle', 'In Use', 'Maintenance', 'Out of Service']
        status_weights = [0.45, 0.30, 0.15, 0.10]  # 45% idle, 30% in use, etc.
        
        funding_sources = [
            'SMAM - Sub-Mission on Agricultural Mechanization',
            'RKVY - Rashtriya Krishi Vikas Yojana',
            'State Agricultural Development Scheme',
            'Central Sector Scheme',
            'NABARD Subsidy',
            'PM-KMY Fund',
            'Own Fund by CHC',
            'Bank Loan',
            None
        ]
        
        for chc in self.data['chcs']:
            # Determine number of machines based on CHC age and activity
            months_active = (timezone.now() - chc.registration_date).days / 30
            base_machines = self.config['machines_per_chc']
            num_machines = int(base_machines * (0.8 + 0.4 * random.random()))  # 80-120% of base
            
            for i in range(num_machines):
                machine_type = random.choice(list(machine_specs.keys()) if random.random() > 0.2 
                                           else ['Other', 'Cultivator', 'Disc Harrow'])
                
                # Get specs for this type
                specs = machine_specs.get(machine_type, default_spec)
                
                # Generate unique machine code
                machine_code = self.gen.generate_unique_machine_code(chc.id, machine_type)
                
                # Generate purchase year (weighted towards recent years)
                year_weights = [0.05, 0.10, 0.15, 0.25, 0.30, 0.15]  # 2019-2024 weights
                purchase_year = random.choices(range(2019, 2025), weights=year_weights)[0]
                
                # Calculate service dates
                today = date.today()
                last_serviced = self.gen.fake.date_between(start_date='-1y', end_date='-1M')
                service_interval = random.randint(180, 365)  # 6-12 months
                next_service = last_serviced + timedelta(days=service_interval)
                
                # If next service is in the past, make it due soon
                if next_service < today:
                    next_service = today + timedelta(days=random.randint(1, 30))
                
                machine = Machine.objects.create(
                    machine_code=machine_code,
                    chc=chc,
                    machine_name=f"{machine_type} {random.choice(['Pro', 'Deluxe', 'Standard', 'Plus'])}",
                    machine_type=machine_type,
                    purchase_year=purchase_year,
                    funding_source=random.choice(funding_sources),
                    status=random.choices(status_choices, weights=status_weights)[0],
                    total_hours_used=0,  # Will be updated after usage
                    last_serviced_date=last_serviced,
                    next_service_due=next_service,
                )
                self.data['machines'].append(machine)
                
                if self.config['verbose'] and i % 5 == 0:
                    self.stdout.write(f"    Created machine: {machine.machine_name} for {chc.chc_name}")
            
            # Update CHC machine count
            chc.total_machines = Machine.objects.filter(chc=chc).count()
            chc.save()
        
        self.stdout.write(self.style.SUCCESS(f"  ✓ Created {len(self.data['machines'])} machines"))

    def create_bookings(self):
        """Create bookings with realistic patterns and no conflicts."""
        
        # Farmer data pools for consistency
        villages = [
            'Rampur', 'Nagla', 'Bhagwanpur', 'Shahpur', 'Fatehpur', 'Sultanpur', 
            'Raipur', 'Gopalpur', 'Kishanpur', 'Malikpur', 'Dhamora', 'Bichpuri',
            'Khera', 'Majra', 'Dhani', 'Bassi', 'Jagir', 'Kalan', 'Khurd'
        ]
        
        crops = ['Wheat', 'Paddy', 'Sugarcane', 'Maize', 'Cotton', 'Mustard', 
                'Bajra', 'Jowar', 'Gram', 'Barley', 'Sunflower', 'Soybean']
        
        seasons = ['Rabi', 'Kharif', 'Zaid']
        
        purpose_templates = [
            "Sowing of {crop} in {village} for {season} season",
            "Land preparation for {crop} cultivation in {village}",
            "Harvesting of {crop} at {village} farm",
            "Plowing for {crop} planting in {village}",
            "Residue management after {crop} harvest in {village}",
            "Leveling of field for {crop} cultivation in {village}"
        ]
        
        for machine in self.data['machines']:
            # Determine number of bookings based on machine age and type
            months_since_purchase = (timezone.now().date() - date(machine.purchase_year, 1, 1)).days / 30
            base_bookings = self.config['bookings_per_machine']
            num_bookings = int(base_bookings * (0.7 + 0.6 * random.random()))  # 70-130% of base
            
            # Track occupied periods for this machine
            occupied_periods = []
            
            for j in range(num_bookings):
                # Generate booking dates with seasonal patterns
                season = random.choice(seasons)
                if season == 'Rabi':  # Oct-Dec
                    year = random.choice([2024, 2025])
                    start_month = random.randint(10, 12)
                elif season == 'Kharif':  # Jun-Sep
                    year = random.choice([2024, 2025])
                    start_month = random.randint(6, 9)
                else:  # Zaid - Mar-May
                    year = random.choice([2024, 2025])
                    start_month = random.randint(3, 5)
                
                # Create start date with some randomness
                try:
                    start_day = random.randint(1, 25)
                    start_date = date(year, start_month, start_day)
                except ValueError:
                    start_day = random.randint(1, 20)
                    start_date = date(year, start_month, start_day)
                
                # Ensure date is not too far in future
                if start_date > date.today() + timedelta(days=90):
                    start_date = date.today() + timedelta(days=random.randint(1, 60))
                
                # Generate duration based on machine type and crop
                if 'Seeder' in machine.machine_type or 'Drill' in machine.machine_type:
                    duration = random.randint(3, 7)  # Sowing takes less time
                elif 'Harvest' in machine.machine_type or 'Reaper' in machine.machine_type:
                    duration = random.randint(5, 12)  # Harvesting takes more time
                else:
                    duration = random.randint(2, 10)
                
                end_date = start_date + timedelta(days=duration)
                
                # Check for conflicts (allow some overlap only for different statuses)
                conflict = False
                for occ_start, occ_end in occupied_periods[-10:]:  # Check last 10 to save time
                    if not (end_date < occ_start or start_date > occ_end):
                        # If dates overlap, check if it's a minor overlap
                        overlap_days = min(end_date, occ_end) - max(start_date, occ_start)
                        if overlap_days.days > 2:  # Allow small overlaps (1-2 days)
                            conflict = True
                            break
                
                if conflict:
                    continue
                
                occupied_periods.append((start_date, end_date))
                
                # Determine status based on dates
                today = date.today()
                if end_date < today:
                    status = random.choices(
                        ['Completed', 'Cancelled', 'Rejected'],
                        weights=[0.85, 0.10, 0.05]
                    )[0]
                elif start_date <= today <= end_date:
                    status = random.choices(
                        ['Active', 'Approved'],
                        weights=[0.8, 0.2]
                    )[0]
                else:  # Future booking
                    status = random.choices(
                        ['Pending', 'Approved'],
                        weights=[0.3, 0.7]
                    )[0]
                
                # Generate farmer details
                village = random.choice(villages)
                crop = random.choice(crops)
                
                first_name = self.gen.fake.first_name()
                last_name = self.gen.fake.last_name()
                farmer_name = f"{first_name} {last_name}"
                
                # Create purpose text
                purpose = random.choice(purpose_templates).format(
                    crop=crop, village=village, season=season
                )
                
                # Calculate field area (in acres)
                field_area = Decimal(str(random.uniform(1.0, 25.0))).quantize(Decimal('0.01'))
                
                # Generate booking date (usually before start date)
                if start_date > today:
                    booking_date = self.gen.fake.date_time_between(
                        start_date=start_date - timedelta(days=30),
                        end_date=start_date - timedelta(days=1)
                    )
                else:
                    booking_date = self.gen.fake.date_time_between(
                        start_date=start_date - timedelta(days=20),
                        end_date=start_date
                    )
                
                booking = Booking.objects.create(
                    chc=machine.chc,
                    machine=machine,
                    start_date=start_date,
                    end_date=end_date,
                    status=status,
                    farmer_name=farmer_name,
                    farmer_contact=self.gen.generate_unique_phone(),
                    farmer_email=self.gen.generate_unique_email(f"farmer.{first_name}.{last_name}"),
                    farmer_aadhar=self.gen.generate_unique_aadhaar(),
                    field_area=field_area,
                    purpose=purpose,
                    rejection_reason="Farmer documents incomplete" if status == 'Rejected' else None,
                    booking_date=booking_date,
                )
                self.data['bookings'].append(booking)
        
        self.stdout.write(self.style.SUCCESS(f"  ✓ Created {len(self.data['bookings'])} bookings"))

    def create_usage_records(self):
        """Create usage records for completed and active bookings."""
        
        operators = [self.gen.fake.name() for _ in range(50)]
        remarks_templates = [
            "Work completed successfully",
            "Field condition was good",
            "Slight delay due to weather",
            "Machine performed well",
            "Farmer satisfied with service",
            "Some technical issues but resolved",
            "Efficient operation",
            "Worked overtime to complete",
            "Quality work delivered",
            "Farmer requested additional area"
        ]
        
        usage_records = []
        
        for booking in self.data['bookings']:
            if booking.status not in ['Active', 'Completed']:
                continue
            
            # Calculate number of sessions based on booking duration
            booking_days = (booking.end_date - booking.start_date).days
            if booking_days <= 0:
                continue
            
            # More sessions for longer bookings
            if booking_days <= 3:
                num_sessions = 1
            elif booking_days <= 7:
                num_sessions = random.randint(1, 2)
            else:
                num_sessions = random.randint(2, 4)
            
            used_dates = set()
            for session_num in range(num_sessions):
                # Distribute sessions across booking period
                if num_sessions == 1:
                    session_date = booking.start_date + timedelta(days=booking_days // 2)
                else:
                    day_offset = (session_num * booking_days) // num_sessions
                    session_date = booking.start_date + timedelta(days=day_offset)
                
                # Avoid duplicates
                if session_date in used_dates:
                    # Try next day
                    session_date += timedelta(days=1)
                used_dates.add(session_date)
                
                # Generate realistic timings
                if 'Harvest' in booking.machine.machine_type or 'Reaper' in booking.machine.machine_type:
                    # Harvesting often starts early
                    start_hour = random.randint(5, 7)
                else:
                    start_hour = random.randint(7, 9)
                
                # Duration based on machine type and area
                if booking.field_area:
                    # Estimate hours needed (1-3 acres per hour typical)
                    hours_needed = float(booking.field_area) * random.uniform(0.5, 1.5)
                    duration_hours = min(int(hours_needed), 12)  # Cap at 12 hours
                else:
                    duration_hours = random.randint(4, 10)
                
                end_hour = min(start_hour + duration_hours, 19)  # Don't go beyond 7 PM
                
                start_time = datetime.strptime(f"{start_hour}:00", "%H:%M").time()
                end_time = datetime.strptime(f"{end_hour}:00", "%H:%M").time()
                
                # Calculate actual hours worked
                hours_worked = end_hour - start_hour
                
                # Calculate area covered in this session
                if booking.field_area:
                    if num_sessions == 1:
                        session_area = booking.field_area
                    else:
                        # Distribute area across sessions
                        remaining_area = float(booking.field_area) * (1 - session_num / num_sessions)
                        session_area = Decimal(str(max(0.5, remaining_area * random.uniform(0.3, 0.7))))
                else:
                    session_area = Decimal(str(random.uniform(0.5, 5.0))).quantize(Decimal('0.01'))
                
                # Calculate residue managed (tons)
                if 'Straw' in booking.machine.machine_type or 'Baler' in booking.machine.machine_type:
                    residue_per_acre = Decimal(str(random.uniform(1.0, 2.5)))
                else:
                    residue_per_acre = Decimal(str(random.uniform(0.3, 0.8)))
                
                residue_managed = (session_area * residue_per_acre).quantize(Decimal('0.01'))
                
                # Calculate fuel consumption
                if 'Happy Seeder' in booking.machine.machine_type or 'Super Seeder' in booking.machine.machine_type:
                    fuel_per_hour = Decimal(str(random.uniform(4.0, 6.0)))  # Higher fuel consumption
                else:
                    fuel_per_hour = Decimal(str(random.uniform(2.5, 4.5)))
                
                fuel_consumed = (Decimal(str(hours_worked)) * fuel_per_hour).quantize(Decimal('0.1'))
                
                # Generate meter readings
                base_reading = random.randint(1000, 50000)
                meter_diff = Decimal(str(hours_worked * random.uniform(0.8, 1.2)))
                start_meter = Decimal(str(base_reading)).quantize(Decimal('0.1'))
                end_meter = (start_meter + meter_diff).quantize(Decimal('0.1'))
                
                usage = MachineUsage.objects.create(
                    machine=booking.machine,
                    chc=booking.chc,
                    booking=booking,
                    farmer_name=booking.farmer_name,
                    farmer_contact=booking.farmer_contact,
                    farmer_aadhar=booking.farmer_aadhar,
                    usage_date=session_date,
                    start_time=start_time,
                    end_time=end_time,
                    total_hours_used=Decimal(str(hours_worked)),
                    start_meter_reading=start_meter,
                    end_meter_reading=end_meter,
                    gps_lat=booking.chc.latitude + Decimal(str(random.uniform(-0.03, 0.03))).quantize(Decimal('0.000001')),
                    gps_lng=booking.chc.longitude + Decimal(str(random.uniform(-0.03, 0.03))).quantize(Decimal('0.000001')),
                    purpose=booking.purpose,
                    crop_type=booking.purpose.split()[1] if len(booking.purpose.split()) > 1 else 'Unknown',
                    area_covered=session_area,
                    residue_managed=residue_managed,
                    fuel_consumed=fuel_consumed,
                    operator_name=random.choice(operators),
                    remarks=random.choice(remarks_templates) + (f" - Session {session_num + 1}" if num_sessions > 1 else ""),
                )
                usage_records.append(usage)
        
        self.data['usages'] = usage_records
        
        # Update machine totals based on usage records
        self.stdout.write("    Updating machine usage statistics...")
        machine_updates = 0
        for machine in self.data['machines']:
            machine_usages = MachineUsage.objects.filter(machine=machine)
            
            # Calculate total hours
            total_hours = machine_usages.aggregate(total=models.Sum('total_hours_used'))['total'] or 0
            machine.total_hours_used = total_hours
            
            # Update last used date
            last_usage = machine_usages.order_by('-usage_date', '-end_time').first()
            if last_usage:
                last_datetime = datetime.combine(last_usage.usage_date, last_usage.end_time)
                machine.last_used_date = timezone.make_aware(last_datetime) if timezone.is_naive(last_datetime) else last_datetime
                machine_updates += 1
            
            # Update machine status based on recent usage
            if machine.status != 'Out of Service' and machine.status != 'Maintenance':
                if last_usage and (date.today() - last_usage.usage_date).days <= 7:
                    # Recently used
                    if random.random() > 0.3:
                        machine.status = 'In Use'
                elif machine.status == 'In Use' and (not last_usage or (date.today() - last_usage.usage_date).days > 14):
                    # Not used for 2 weeks, likely idle
                    machine.status = 'Idle'
            
            machine.save()
        
        self.stdout.write(self.style.SUCCESS(f"  ✓ Created {len(self.data['usages'])} usage records"))
        self.stdout.write(f"    Updated last_used_date for {machine_updates} machines")

    def create_audit_logs(self):
        """Generate comprehensive audit log entries."""
        
        action_types = ['CREATE', 'UPDATE', 'DELETE', 'APPROVE', 'REJECT', 'LOGIN', 'LOGOUT', 'VIEW']
        tables = ['chc_chc', 'machines_machine', 'bookings_booking', 'usage_machineusage', 'accounts_user']
        
        # Get all users
        users = list(User.objects.all())
        if not users:
            users = [None]  # Allow anonymous actions
        
        # Create logs for each significant action
        log_entries = []
        
        # Logs for machine creations
        # Logs for machine creations
        for machine in self.data['machines'][:50]:  # Sample some machines
            user = random.choice(users) if users and random.random() > 0.3 else None
            
            # Generate timestamp and make it aware
            timestamp_naive = self.gen.fake.date_time_between(
                start_date=machine.created_at - timedelta(minutes=10),
                end_date=machine.created_at + timedelta(minutes=30)
            )
            timestamp = timezone.make_aware(timestamp_naive) if timezone.is_naive(timestamp_naive) else timestamp_naive
            
            AuditLog.objects.create(
                user=user,
                action_type='CREATE',
                table_name='machines_machine',
                record_id=str(machine.id),
                old_value=None,
                new_value={
                    'machine_code': machine.machine_code,
                    'machine_type': machine.machine_type,
                    'status': machine.status,
                    'chc_id': machine.chc.id
                },
                ip_address=self.gen.fake.ipv4() if random.random() > 0.3 else None,
                timestamp=timestamp,
            )
        
        # Logs for booking status changes
        # Logs for booking status changes
        for booking in self.data['bookings']:
            if booking.status in ['Approved', 'Rejected', 'Cancelled']:
                user = User.objects.filter(chc=booking.chc, role='CHC_ADMIN').first()
                if user and random.random() > 0.3:
                    # Generate timestamp and make it aware
                    timestamp_naive = self.gen.fake.date_time_between(
                        start_date=booking.booking_date,
                        end_date=booking.updated_at
                    )
                    timestamp = timezone.make_aware(timestamp_naive) if timezone.is_naive(timestamp_naive) else timestamp_naive
                    
                    AuditLog.objects.create(
                        user=user,
                        action_type=booking.status.upper(),
                        table_name='bookings_booking',
                        record_id=str(booking.id),
                        old_value={'status': 'Pending'} if booking.status != 'Pending' else None,
                        new_value={'status': booking.status},
                        ip_address=self.gen.fake.ipv4(),
                        timestamp=timestamp,
                    )
        
        # Logs for usage records
        # Logs for usage records
        for usage in self.data['usages'][:100]:  # Sample some usage records
            user = random.choice(users) if users and random.random() > 0.4 else None
            
            # Generate timestamp and make it aware
            timestamp_naive = self.gen.fake.date_time_between(
                start_date=usage.created_at - timedelta(minutes=5),
                end_date=usage.created_at + timedelta(minutes=15)
            )
            timestamp = timezone.make_aware(timestamp_naive) if timezone.is_naive(timestamp_naive) else timestamp_naive
            
            AuditLog.objects.create(
                user=user,
                action_type='CREATE',
                table_name='usage_machineusage',
                record_id=str(usage.id),
                old_value=None,
                new_value={
                    'machine_id': usage.machine.id,
                    'hours_used': float(usage.total_hours_used) if usage.total_hours_used else None,
                    'area': float(usage.area_covered) if usage.area_covered else None
                },
                ip_address=self.gen.fake.ipv4() if random.random() > 0.3 else None,
                timestamp=timestamp,
            )
        
        # Login/Logout activities
        # Login/Logout activities
        for user in random.sample(users, min(len(users), 20)):
            num_sessions = random.randint(5, 30)
            for _ in range(num_sessions):
                # Generate naive datetime from Faker
                login_time_naive = self.gen.fake.date_time_between(start_date='-3M', end_date='now')
                
                # Make it timezone aware (assuming UTC)
                login_time = timezone.make_aware(login_time_naive) if timezone.is_naive(login_time_naive) else login_time_naive
                
                logout_time_naive = login_time_naive + timedelta(hours=random.randint(1, 8))
                logout_time = timezone.make_aware(logout_time_naive) if timezone.is_naive(logout_time_naive) else logout_time_naive
                
                # Login log
                AuditLog.objects.create(
                    user=user,
                    action_type='LOGIN',
                    table_name='accounts_user',
                    record_id=str(user.id),
                    old_value=None,
                    new_value={'session_start': login_time.isoformat()},
                    ip_address=self.gen.fake.ipv4(),
                    timestamp=login_time,
                )
                
                # Logout log (if not too recent)
                if logout_time < timezone.now():
                    AuditLog.objects.create(
                        user=user,
                        action_type='LOGOUT',
                        table_name='accounts_user',
                        record_id=str(user.id),
                        old_value=None,
                        new_value={'session_end': logout_time.isoformat()},
                        ip_address=self.gen.fake.ipv4(),
                        timestamp=logout_time,
                    )
        
        self.stdout.write(self.style.SUCCESS(f"  ✓ Created {AuditLog.objects.count()} audit logs"))

    def create_notifications(self):
        """Create notifications for users with realistic scenarios."""
        
        notification_templates = [
            {
                'title': "New Booking Request",
                'message': "A new booking request has been received for {machine} from {farmer}.",
                'type': 'BOOKING_REQUEST'
            },
            {
                'title': "Booking {status}",
                'message': "Your booking for {machine} has been {status}.",
                'type': 'BOOKING_UPDATE'
            },
            {
                'title': "Machine Service Due",
                'message': "Machine {machine} is due for service on {date}. Please schedule maintenance.",
                'type': 'MAINTENANCE'
            },
            {
                'title': "Usage Report Available",
                'message': "Daily usage report for {machine} is now available. Total hours: {hours}.",
                'type': 'REPORT'
            },
            {
                'title': "Low Fuel Alert",
                'message': "Machine {machine} fuel level is low. Please refill.",
                'type': 'ALERT'
            },
            {
                'title': "Booking Completed",
                'message': "Booking #{booking_id} for {machine} has been completed successfully.",
                'type': 'BOOKING_COMPLETE'
            },
            {
                'title': "Payment Received",
                'message': "Payment of ₹{amount} received for booking #{booking_id}.",
                'type': 'PAYMENT'
            },
            {
                'title': "New Farmer Registration",
                'message': "New farmer {farmer} has registered in your area.",
                'type': 'REGISTRATION'
            },
            {
                'title': "System Update",
                'message': "System will be under maintenance on {date} from 2 AM to 4 AM.",
                'type': 'SYSTEM'
            }
        ]
        
        users = list(User.objects.filter(role='CHC_ADMIN'))
        
        for user in users:
            # Determine number of notifications based on user activity
            num_notifications = random.randint(15, 40)
            
            for i in range(num_notifications):
                template = random.choice(notification_templates)
                
                # Generate dynamic content
                context = {}
                
                # Get machines for this user's CHC
                if user.chc:
                    machines = Machine.objects.filter(chc=user.chc)
                    if machines.exists():
                        machine = random.choice(machines)
                        context['machine'] = machine.machine_name
                        context['machine_code'] = machine.machine_code
                
                # Get farmers from bookings
                if user.chc:
                    farmers = Booking.objects.filter(chc=user.chc).values_list('farmer_name', flat=True).distinct()
                    if farmers:
                        context['farmer'] = random.choice(list(farmers))
                    else:
                        context['farmer'] = self.gen.fake.name()
                else:
                    context['farmer'] = self.gen.fake.name()
                
                # Get bookings for this CHC
                if user.chc:
                    bookings = Booking.objects.filter(chc=user.chc)
                    if bookings.exists():
                        booking = random.choice(bookings)
                        context['booking_id'] = booking.id
                
                # Random amounts for payments
                context['amount'] = random.randint(500, 5000)
                
                # Future dates for maintenance
                future_date = date.today() + timedelta(days=random.randint(1, 30))
                context['date'] = future_date.strftime('%d %b %Y')
                
                # Random hours for reports
                context['hours'] = round(random.uniform(2.5, 12.5), 1)
                
                # Fill in the template
                try:
                    title = template['title'].format(**context)
                    message = template['message'].format(**context)
                except KeyError:
                    # If formatting fails, use the template as is
                    title = template['title']
                    message = template['message']
                
                # Random read status (70% read for older notifications)
                # Random read status (70% read for older notifications)
                created_at_naive = self.gen.fake.date_time_between(start_date='-2M', end_date='now')
                created_at = timezone.make_aware(created_at_naive) if timezone.is_naive(created_at_naive) else created_at_naive
                days_old = (timezone.now() - created_at).days
                
                if days_old > 7:
                    is_read = random.random() < 0.9  # 90% read for old notifications
                elif days_old > 1:
                    is_read = random.random() < 0.6  # 60% read for recent
                else:
                    is_read = random.random() < 0.3  # 30% read for today
                
                # Generate related URL
                if 'BOOKING' in template['type']:
                    related_url = f"/dashboard/bookings/{context.get('booking_id', '')}"
                elif 'MACHINE' in template['type'] or 'MAINTENANCE' in template['type']:
                    related_url = f"/dashboard/machines/{context.get('machine_code', '')}"
                elif 'REPORT' in template['type']:
                    related_url = "/dashboard/reports"
                else:
                    related_url = "/dashboard"
                
                Notification.objects.create(
                    user=user,
                    title=title[:255],  # Truncate if too long
                    message=message,
                    notification_type=template['type'],
                    related_url=related_url,
                    is_read=is_read,
                    created_at=created_at,
                )
        
        self.stdout.write(self.style.SUCCESS(f"  ✓ Created {Notification.objects.count()} notifications"))

    def validate_data(self):
        """Validate data integrity and relationships."""
        
        self.stdout.write("    Validating data integrity...")
        
        validation_checks = [
            # Check 1: All machines belong to valid CHCs
            {
                'name': 'Machine-CHC relationships',
                'check': all(m.chc in self.data['chcs'] for m in self.data['machines']),
                'critical': True
            },
            # Check 2: All bookings have valid machines and CHCs
            {
                'name': 'Booking relationships',
                'check': all(b.machine in self.data['machines'] and b.chc in self.data['chcs'] 
                           for b in self.data['bookings']),
                'critical': True
            },
            # Check 3: All usage records have valid bookings (where applicable)
            {
                'name': 'Usage relationships',
                'check': all(u.machine in self.data['machines'] and u.chc in self.data['chcs']
                           and (u.booking is None or u.booking in self.data['bookings'])
                           for u in self.data['usages']),
                'critical': True
            },
            # Check 4: No overlapping active bookings for same machine
            {
                'name': 'Booking conflict check',
                'check': self.check_booking_conflicts(),
                'critical': False
            },
            # Check 5: Machine usage hours don't exceed booking periods
            {
                'name': 'Usage within booking periods',
                'check': self.check_usage_within_bookings(),
                'critical': False
            },
            # Check 6: All CHC admin users have assigned CHCs
            {
                'name': 'CHC admin assignments',
                'check': all(u.chc is not None for u in self.data['users'] if u.role == 'CHC_ADMIN'),
                'critical': True
            },
        ]
        
        all_passed = True
        for check in validation_checks:
            if check['check']:
                self.stdout.write(f"      ✓ {check['name']}: PASSED")
            else:
                all_passed = False
                if check['critical']:
                    self.stdout.write(self.style.ERROR(f"      ✗ {check['name']}: FAILED (CRITICAL)"))
                else:
                    self.stdout.write(self.style.WARNING(f"      ⚠ {check['name']}: WARNING - Non-critical issue"))
        
        if all_passed:
            self.stdout.write(self.style.SUCCESS("    ✓ All critical validations passed!"))
        else:
            self.stdout.write(self.style.WARNING("    ⚠ Some non-critical validation issues found"))
    
    def check_booking_conflicts(self):
        """Check for overlapping active bookings on the same machine."""
        machine_bookings = {}
        for booking in self.data['bookings']:
            if booking.status in ['Active', 'Approved']:
                if booking.machine.id not in machine_bookings:
                    machine_bookings[booking.machine.id] = []
                machine_bookings[booking.machine.id].append((booking.start_date, booking.end_date))
        
        # Check for overlaps
        for machine_id, periods in machine_bookings.items():
            periods.sort()
            for i in range(len(periods) - 1):
                if periods[i][1] >= periods[i + 1][0]:
                    # Overlap found, but allow same-day transitions
                    if (periods[i][1] - periods[i + 1][0]).days >= 0:
                        # Actual overlap
                        return False
        return True
    
    def check_usage_within_bookings(self):
        """Check that usage records don't exceed their booking periods."""
        for usage in self.data['usages']:
            if usage.booking:
                if usage.usage_date < usage.booking.start_date or usage.usage_date > usage.booking.end_date:
                    return False
        return True

    def print_summary(self):
        """Print comprehensive summary of created data."""
        
        self.stdout.write(self.style.SUCCESS("\n" + "=" * 60))
        self.stdout.write(self.style.SUCCESS("POPULATION SUMMARY"))
        self.stdout.write(self.style.SUCCESS("=" * 60))
        
        # Overall counts
        self.stdout.write("\n📊 OVERALL STATISTICS:")
        self.stdout.write(f"  • CHCs: {len(self.data['chcs'])}")
        self.stdout.write(f"  • Users: {len(self.data['users'])}")
        self.stdout.write(f"  • Machines: {len(self.data['machines'])}")
        self.stdout.write(f"  • Bookings: {len(self.data['bookings'])}")
        self.stdout.write(f"  • Usage Records: {len(self.data['usages'])}")
        self.stdout.write(f"  • Audit Logs: {AuditLog.objects.count()}")
        self.stdout.write(f"  • Notifications: {Notification.objects.count()}")
        
        # CHC-wise breakdown
        self.stdout.write("\n🏭 CHC-WISE BREAKDOWN:")
        for chc in self.data['chcs'][:5]:  # Show first 5 CHCs
            machine_count = Machine.objects.filter(chc=chc).count()
            booking_count = Booking.objects.filter(chc=chc).count()
            usage_count = MachineUsage.objects.filter(chc=chc).count()
            self.stdout.write(f"  • {chc.chc_name}:")
            self.stdout.write(f"      Machines: {machine_count}, Bookings: {booking_count}, Usage: {usage_count}")
        
        if len(self.data['chcs']) > 5:
            self.stdout.write(f"      ... and {len(self.data['chcs']) - 5} more CHCs")
        
        # Status distribution
        self.stdout.write("\n📈 STATUS DISTRIBUTION:")
        
        # Machine status
        machine_statuses = {}
        for machine in self.data['machines']:
            machine_statuses[machine.status] = machine_statuses.get(machine.status, 0) + 1
        self.stdout.write("  Machine Status:")
        for status, count in machine_statuses.items():
            percentage = (count / len(self.data['machines'])) * 100
            self.stdout.write(f"      {status}: {count} ({percentage:.1f}%)")
        
        # Booking status
        booking_statuses = {}
        for booking in self.data['bookings']:
            booking_statuses[booking.status] = booking_statuses.get(booking.status, 0) + 1
        self.stdout.write("  Booking Status:")
        for status, count in booking_statuses.items():
            percentage = (count / len(self.data['bookings'])) * 100
            self.stdout.write(f"      {status}: {count} ({percentage:.1f}%)")
        
        # Machine type distribution
        self.stdout.write("\n🔧 MACHINE TYPE DISTRIBUTION:")
        machine_types = {}
        for machine in self.data['machines']:
            machine_types[machine.machine_type] = machine_types.get(machine.machine_type, 0) + 1
        
        # Show top 5 machine types
        sorted_types = sorted(machine_types.items(), key=lambda x: x[1], reverse=True)[:5]
        for mtype, count in sorted_types:
            percentage = (count / len(self.data['machines'])) * 100
            self.stdout.write(f"      {mtype}: {count} ({percentage:.1f}%)")
        
        # Usage statistics
        if self.data['usages']:
            total_hours = sum((u.total_hours_used or 0) for u in self.data['usages'])
            total_area = sum((u.area_covered or 0) for u in self.data['usages'])
            total_fuel = sum((u.fuel_consumed or 0) for u in self.data['usages'])
            
            self.stdout.write("\n⏱️  USAGE STATISTICS:")
            self.stdout.write(f"      Total Hours Used: {total_hours:.1f}")
            self.stdout.write(f"      Total Area Covered: {total_area:.2f} acres")
            self.stdout.write(f"      Total Fuel Consumed: {total_fuel:.1f} liters")
            self.stdout.write(f"      Average Hours per Usage: {total_hours/len(self.data['usages']):.2f}")
        
        # Time range
        if self.data['bookings']:
            first_booking = min(b.booking_date for b in self.data['bookings'])
            last_booking = max(b.booking_date for b in self.data['bookings'])
            self.stdout.write(f"\n📅 DATA TIMESPAN:")
            self.stdout.write(f"      First Booking: {first_booking.strftime('%d %b %Y')}")
            self.stdout.write(f"      Last Booking: {last_booking.strftime('%d %b %Y')}")
        
        self.stdout.write("")
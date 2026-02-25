import os
import django
import sys

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm_backend.settings')
django.setup()

from rest_framework.test import APIClient
from accounts.models import User
from bookings.models import Booking
from chc.models import CHC
from machines.models import Machine

def run_test():
    client = APIClient()
    
    # Try to find user `adm_lud_43`
    try:
        user = User.objects.get(username='adm_lud_43')
    except User.DoesNotExist:
        print("User adm_lud_43 not found!")
        # let's find any chc admin
        user = User.objects.filter(role='CHC_ADMIN').first()
        if not user:
            print("No CHC_ADMIN found.")
            return

    # Ensure user has a CHC
    if not user.chc:
        print(f"User {user} has no CHC.")
        return

    # Find a pending booking for this CHC
    booking = Booking.objects.filter(chc=user.chc, status='Pending').first()
    if not booking:
        print(f"No pending booking found for CHC {user.chc}.")
        # Let's create one for testing
        machine = Machine.objects.filter(chc=user.chc).first()
        if not machine:
            print("No machine found either")
            return
        from datetime import date
        booking = Booking.objects.create(
            chc=user.chc, 
            machine=machine, 
            start_date=date.today(), 
            end_date=date.today(), 
            farmer_name='Test Farmer',
            farmer_contact='1234567890',
            farmer_aadhar='123456789012',
            status='Pending'
        )

    # Authenticate
    client.force_authenticate(user=user)
    
    print(f"Testing action handover on Booking ID {booking.id}")
    # Make request
    response = client.patch(f'/api/v1/bookings/chc/{booking.id}/action/', data={'action': 'handover', 'notes': ''}, format='json')
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.content}")

if __name__ == '__main__':
    run_test()

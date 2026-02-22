import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ehr_system.settings')
django.setup()

from chc.models import CHC
from accounts.models import User
from django.db import transaction

def run_test():
    with transaction.atomic():
        # Clean up existing test cases
        CHC.objects.filter(chc_name="TEST CHC ASSIGNMENT").delete()
        User.objects.filter(username__in=["test_admin_A", "test_admin_B"]).delete()

        print("Creating Test CHC...")
        chc = CHC.objects.create(
            chc_name="TEST CHC ASSIGNMENT",
            state="Test State",
            district="Test District",
            pincode="123456",
            email="testchc@example.com"
        )
        
        print(f"CHC created: {chc.chc_name}")
        
        print("Creating Test Admin A...")
        admin_a = User.objects.create_user(
            username="test_admin_A",
            password="password123",
            email="test_a@example.com",
            role="CHC_ADMIN",
            chc=chc
        )
        
        print(f"Admin A created and assigned. Current CHC Admin: {chc.admin.username}")
        assert chc.admin.username == "test_admin_A"
        
        print("Creating Test Admin B...")
        admin_b = User.objects.create_user(
            username="test_admin_B",
            password="password123",
            email="test_b@example.com",
            role="CHC_ADMIN"
        )
        
        print("Now executing transactional reassignment logic (simulating AssignAdminView)...")
        # Simulating AssignAdminView
        existing_admins = User.objects.filter(chc=chc, role='CHC_ADMIN')
        for admin in existing_admins:
            admin.chc = None
            admin.save()
            print(f"Detached old admin: {admin.username}")
        
        admin_b.chc = chc
        admin_b.save()
        print(f"Assigned new admin: {admin_b.username}")
        
        chc.refresh_from_db()
        print(f"Current CHC Admin now: {chc.admin.username}")
        assert chc.admin.username == "test_admin_B"
        
        old_admin = User.objects.get(username="test_admin_A")
        assert old_admin.chc is None
        print(f"Verified old admin A has no CHC: {old_admin.chc}")

        print("--- TEST PASSED SUCCESSFULLY ---")
        
        # Cleanup
        chc.delete()
        admin_b.delete()
        old_admin.delete()

if __name__ == '__main__':
    run_test()

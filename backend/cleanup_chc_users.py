import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm_backend.settings')
django.setup()

from accounts.models import User
from chc.models import CHC

def cleanup_chc_users():
    print("Starting CHC User Cleanup...")
    # 1. Remove all Staff roles for CHCs to enforce only CHC_ADMIN (assuming staff role is also 'CHC_ADMIN' in DB but maybe marked otherwise? No, in JSON `staff_` usernames have role 'CHC_ADMIN')
    # Actually, the user says "remove the staff and if 2 or more admins are there for each chc then only leave the ffirst one"
    # Looking at JSON: usernames start with 'staff_' or 'admin_'. Or we can just keep the first 'CHC_ADMIN' per CHC and delete the rest.
    
    chcs = CHC.objects.all()
    total_deleted = 0
    total_kept = 0
    
    for chc in chcs:
        # Get all users assigned to this CHC, ordered by date_joined
        users = User.objects.filter(chc=chc, role='CHC_ADMIN').order_by('date_joined')
        
        if users.exists():
            # Keep the first one
            first_admin = users.first()
            total_kept += 1
            
            # Identify the rest
            excess_users = users.exclude(id=first_admin.id)
            count = excess_users.count()
            
            if count > 0:
                print(f"CHC {chc.chc_name}: Keeping {first_admin.username}, Deleting {count} excess users.")
                # Delete them
                for u in excess_users:
                    u.delete()
                total_deleted += count
                
    print(f"Cleanup complete. Kept {total_kept} admins. Deleted {total_deleted} excess users.")

if __name__ == '__main__':
    cleanup_chc_users()

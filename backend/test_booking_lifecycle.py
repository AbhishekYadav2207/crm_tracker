import requests
import json
import sys

BASE_URL = "http://localhost:8000/api/v1"

# Credentials
CHC_USERNAME = "admin_ludhiana"
CHC_PASSWORD = "admin123"

def run_lifecycle_test():
    with open("lifecycle_test.log", "w", encoding="utf-8") as f:
        def log(msg):
            print(msg)
            f.write(msg + "\n")

        def print_res(name, response):
            status = "[OK]" if response.status_code < 400 else "[FAIL]"
            log(f"{status} {name} ({response.status_code})")
            if response.status_code >= 400:
                log(f"    Error: {response.text[:500]}...") # Increased to 500

        log("--- Starting Booking Lifecycle Test ---")
        
        # 1. Login
        session = requests.Session()
        try:
            res = session.post(f"{BASE_URL}/auth/login/", data={'username': CHC_USERNAME, 'password': CHC_PASSWORD})
            print_res("Login", res)
            if res.status_code != 200:
                return
            token = res.json()['access']
            headers = {'Authorization': f'Bearer {token}'}
        except Exception as e:
            log(f"Login failed: {e}")
            return

        # 2. Get a Machine (to book)
        try:
            res = session.get(f"{BASE_URL}/machines/", headers=headers)
            print_res("Get Machines", res)
            data = res.json()
            machines = data.get('results', data) if isinstance(data, dict) else data
            
            if not machines:
                log("    No machines found. Creating one...")
                machine_data = {
                    "machine_code": "TEST-001",
                    "machine_name": "Test Machine",
                    "machine_type": "Super Seeder",
                    "purchase_year": 2023,
                    "status": "Idle"
                }
                res = session.post(f"{BASE_URL}/machines/", json=machine_data, headers=headers)
                print_res("Create Machine", res)
                if res.status_code != 201:
                    log("    [FAIL] Could not create machine")
                    return
                machine_id = res.json()['id']
            else:
                machine_id = machines[0]['id']
        except Exception as e:
            log(f"Get/Create Machines failed: {e}")
            return
        
        # 3. Create a Booking (Public)
        booking_data = {
            "machine": machine_id,
            "start_date": "2026-03-01",
            "end_date": "2026-03-05",
            "farmer_name": "Lifecycle Tester",
            "farmer_contact": "9998887776",
            "farmer_email": "test@example.com",
            "farmer_aadhar": "123412341234",
            "purpose": "Test Lifecycle"
        }
        res = requests.post(f"{BASE_URL}/bookings/public/create/", json=booking_data) 
        print_res("Create Booking", res)
        if res.status_code != 201:
            return
        booking_id = res.json()['id']
        log(f"    Booking ID: {booking_id}")
        
        # 4. CHC Admin - Approve
        res = session.patch(f"{BASE_URL}/bookings/chc/{booking_id}/action/", json={'action': 'approve'}, headers=headers)
        print_res("Approve Booking", res)
        
        # 5. CHC Admin - Handover
        res = session.patch(f"{BASE_URL}/bookings/chc/{booking_id}/action/", json={'action': 'handover'}, headers=headers)
        print_res("Handover Booking (Active)", res)
        
        # 6. CHC Admin - Complete
        res = session.patch(f"{BASE_URL}/bookings/chc/{booking_id}/action/", json={'action': 'complete'}, headers=headers)
        print_res("Complete Booking", res)
        
        # 7. Check Final Status
        res = session.get(f"{BASE_URL}/bookings/chc/", headers=headers)
        data = res.json()
        bookings = data.get('results', data) if isinstance(data, dict) else data
        
        our_booking = next((b for b in bookings if b['id'] == booking_id), None)
        if our_booking:
            log(f"    Final Status: {our_booking['status']}")
            if our_booking['status'] == 'Completed':
                 log("    [SUCCESS] Lifecycle Verified")
            else:
                 log("    [FAIL] Status Mismatch")
        else:
            log("    [FAIL] Booking not found in list")

if __name__ == "__main__":
    run_lifecycle_test()

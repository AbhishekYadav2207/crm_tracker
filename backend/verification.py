import requests
import json

BASE_URL = "http://127.0.0.1:8000/api/v1"
MACHINE_ID = None
CHC_ID = None

def print_res(name, response):
    status = "[OK]" if response.status_code < 400 else "[FAIL]"
    print(f"{status} {name} ({response.status_code})")
    if response.status_code >= 400:
        print(f"    Error: {response.text[:200]}...")

def verify_endpoints():
    global MACHINE_ID, CHC_ID
    
    print("=== STARTING VERIFICATION ===\n")

    # 1. CHC Search
    print("--- 1. CHC Search ---")
    # Test strict filter
    res = requests.get(f"{BASE_URL}/chc/public/search/?district=Ludhiana")
    print_res("Search by District (Strict)", res)
    
    # Test text search (if applicable)
    res = requests.get(f"{BASE_URL}/chc/public/search/?search=Ludhiana")
    print_res("Search by Text (Q)", res)
    
    data = res.json()
    if 'results' in data and len(data['results']) > 0:
        CHC_ID = data['results'][0]['id']
        print(f"    captured CHC_ID: {CHC_ID}")
    
    # 2. Machines Public
    print("\n--- 2. Machines ---")
    res = requests.get(f"{BASE_URL}/machines/public/?chc={CHC_ID}")
    print_res("List Public Machines", res)
    
    data = res.json()
    results = data.get('results', [])
    if len(results) > 0:
        MACHINE_ID = results[0]['id']
        print(f"    captured MACHINE_ID: {MACHINE_ID}")

    if not MACHINE_ID:
        print("❌ Cannot proceed with Booking test (No Machine ID found)")
        return

    # 3. Create Booking
    print("\n--- 3. Create Booking ---")
    booking_data = {
        "machine": MACHINE_ID,
        "start_date": "2026-03-01",
        "end_date": "2026-03-05",
        "farmer_name": "Test Farmer",
        "farmer_contact": "9876543210",
        "farmer_email": "test@farmer.com",
        "farmer_aadhar": "123412341234",
        "purpose": "Test Booking",
        "field_area": 10.5
    }
    headers = {'Content-Type': 'application/json'}
    res = requests.post(f"{BASE_URL}/bookings/public/create/", data=json.dumps(booking_data), headers=headers)
    print_res("Create Booking", res)

    # 4. Auth flow
    print("\n--- 4. Auth ---")
    login_data = {"username": "govt_admin", "password": "admin123"}
    res = requests.post(f"{BASE_URL}/auth/login/", data=json.dumps(login_data), headers=headers)
    print_res("Login Govt Admin", res)
    
    token = None
    if res.status_code == 200:
        token = res.json().get('access')
        print("    captured Token (Govt Admin)")
    
    if token:
        auth_headers = {'Authorization': f'Bearer {token}'}
        
        # 5. Dashboard Stats
        print("\n--- 5. Dashboards ---")
        res = requests.get(f"{BASE_URL}/analytics/govt/dashboard/", headers=auth_headers)
        print_res("Govt Dashboard Stats", res)

    # 6. CHC Admin Workflow
    print("\n--- 6. CHC Admin Workflow ---")
    chc_login_data = {"username": "admin_ludhiana", "password": "admin123"} # Default from population script
    res = requests.post(f"{BASE_URL}/auth/login/", data=json.dumps(chc_login_data), headers=headers)
    print_res("Login CHC Admin", res)
    
    chc_token = None
    if res.status_code == 200:
        chc_token = res.json().get('access')
        print("    captured CHC Token")

    if chc_token:
        chc_headers = {'Authorization': f'Bearer {chc_token}', 'Content-Type': 'application/json'}
        
        # Get Bookings
        res = requests.get(f"{BASE_URL}/bookings/chc/", headers=chc_headers)
        print_res("List CHC Bookings", res)
        
        bookings_data = res.json()
        bookings_list = bookings_data.get('results', bookings_data) if isinstance(bookings_data, dict) else bookings_data
        
        booking_to_approve = None
        if isinstance(bookings_list, list) and len(bookings_list) > 0:
            # Find a pending booking
            for b in bookings_list:
                if b['status'] == 'Pending':
                    booking_to_approve = b['id']
                    break
        
        if booking_to_approve:
            print(f"    Found Pending Booking ID: {booking_to_approve}")
            # Approve It
            action_data = {"action": "approve", "notes": "Verified by Script"}
            res = requests.put(f"{BASE_URL}/bookings/chc/{booking_to_approve}/action/", data=json.dumps(action_data), headers=chc_headers)
            print_res("Approve Booking", res)
        else:
            print("    No pending booking found to approve (Create one first)")

if __name__ == "__main__":
    import sys
    original_stdout = sys.stdout
    with open('verification.log', 'w', encoding='utf-8') as f:
        sys.stdout = f
        try:
            verify_endpoints()
        except requests.exceptions.ConnectionError:
            print("❌ Could not connect to server. Is it running?")
        finally:
            sys.stdout = original_stdout

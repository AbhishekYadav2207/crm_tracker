import requests
import json

BASE_URL = "http://127.0.0.1:8000/api/v1"
MACHINE_ID = None
CHC_ID = None

def print_res(name, response):
    status = "✅" if response.status_code < 400 else "❌"
    print(f"\n[{status}] {name} ({response.status_code})")
    if response.status_code >= 400:
        print(f"    Error: {response.text}")
    else:
        # print first 100 chars
        print(f"    Response: {response.text[:200]}...")

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
    res = requests.get(f"{BASE_URL}/machines/public/")
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
        print("    captured Token")
    
    if token:
        auth_headers = {'Authorization': f'Bearer {token}'}
        
        # 5. Dashboard Stats
        print("\n--- 5. Dashboards ---")
        res = requests.get(f"{BASE_URL}/analytics/govt/dashboard/", headers=auth_headers)
        print_res("Govt Dashboard Stats", res)
        
        # 6. Machines Auth
        res = requests.get(f"{BASE_URL}/machines/", headers=auth_headers)
        print_res("Admin Machine List", res)

if __name__ == "__main__":
    try:
        verify_endpoints()
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to server. Is it running?")

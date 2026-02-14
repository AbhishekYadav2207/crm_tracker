# CRM Project API Documentation

This document provides a detailed explanation of each API endpoint in the system.

## 1. Analytics

### GET /api/v1/analytics/chc/dashboard/
- **Description**: Provides dashboard statistics for a specific CHC Administrator.
- **Authentication**: Required (CHC Admin role).
- **Parameters**: None.
- **Response**: JSON object containing:
  - `total_machines`: Total number of machines in the CHC.
  - `machines_available`: Number of machines currently idle.
  - `machines_in_use`: Number of machines currently in use.
  - `pending_bookings`: Number of bookings awaiting approval.
  - `active_bookings`: Number of bookings currently active.

### GET /api/v1/analytics/govt/dashboard/
- **Description**: Provides aggregated statistics for the Government Administrator dashboard.
- **Authentication**: Required (Government Admin role).
- **Parameters**: None.
- **Response**: JSON object containing:
  - `total_chcs`: Total number of active CHCs.
  - `total_machines`: Total number of machines across all CHCs.
  - `total_bookings`: Total number of booking requests.
  - `total_usage_hours`: Cumulative machine usage hours.
  - `total_residue_managed`: Total tons of residue managed.
  - `total_area_covered`: Total acres of land covered.

### GET /api/v1/analytics/machines/
- **Description**: Provides analytics specifically related to machine types and status breakdown.
- **Authentication**: Required (Authenticated User).
- **Parameters**: None.
- **Response**: JSON object containing:
  - `machine_types`: List of machine types with their counts.
  - `status_breakdown`: Count of machines in each status (Idle, In Use, Maintenance, etc.).

## 2. Authentication (Auth)

### POST /api/v1/auth/login/
- **Description**: Authenticate a user and obtain JWT access and refresh tokens.
- **Authentication**: Public.
- **Body Parameters**:
  - `username`: User's username.
  - `password`: User's password.
- **Response**: `access` token (short-lived) and `refresh` token (long-lived).

### POST /api/v1/auth/register/
- **Description**: Register a new CHC Administrator.
- **Authentication**: Public (or could be restricted to existing Admins depending on policy).
- **Body Parameters**: `username`, `password`, `email`, `first_name`, `last_name`, `phone_no`.
- **Response**: User details upon successful creation.

### POST /api/v1/auth/token/refresh/
- **Description**: Obtain a new access token using a valid refresh token.
- **Authentication**: Public.
- **Body Parameters**: `refresh`: The refresh token.
- **Response**: New `access` token.

### GET /api/v1/auth/profile/
- **Description**: Retrieve the profile of the currently logged-in user.
- **Authentication**: Required (Authenticated User).
- **Response**: User details including role, CHC association, and contact info.

### PUT / PATCH /api/v1/auth/profile/
- **Description**: Update the profile of the currently logged-in user.
- **Authentication**: Required (Authenticated User).
- **Body Parameters**: Fields to update (e.g., `first_name`, `last_name`, `phone_no`).

## 3. Bookings

### POST /api/v1/bookings/public/create/
- **Description**: Allow a farmer (public user) to submit a booking request.
- **Authentication**: Public.
- **Body Parameters**:
  - `machine`: ID of the machine to book.
  - `start_date`, `end_date`: Booking period.
  - `farmer_name`, `farmer_contact`, `farmer_email`, `farmer_aadhar`.
  - `purpose`, `field_area`.
- **Response**: Created booking details with `Pending` status.

### GET /api/v1/bookings/public/{booking_id}/status/
- **Description**: Check the status of a specific booking using its ID.
- **Authentication**: Public.
- **Response**: Current status (`Pending`, `Approved`, `Rejected`, etc.) and basic details.

### GET /api/v1/bookings/chc/
- **Description**: List all bookings associated with the logged-in CHC Admin's CHC.
- **Authentication**: Required (CHC Admin).
- **Parameters**: Supports filtering by status or machine ordering.
- **Response**: List of bookings with full details.

### PUT / PATCH /api/v1/bookings/chc/{id}/action/
- **Description**: CHC Admin approves or rejects a booking request.
- **Authentication**: Required (CHC Admin of the relevant CHC).
- **Body Parameters**:
  - `action`: "approve" or "reject".
  - `notes`: Reason for rejection or additional notes.
- **Response**: Updated booking status.

## 4. Custom Hiring Centres (CHC)

### GET /api/v1/chc/
- **Description**: List all Custom Hiring Centres.
- **Authentication**: Required (Authenticated User).
- **Response**: List of CHCs with admin contact details and location.

### POST /api/v1/chc/
- **Description**: Register a new Custom Hiring Centre.
- **Authentication**: Required (Authenticated User - likely restricted to Govt Admin).
- **Body Parameters**: `chc_name`, `state`, `district`, `location`, `pincode`, `admin_name`, etc.

### GET /api/v1/chc/public/search/
- **Description**: Publicly search for CHCs based on location.
- **Authentication**: Public.
- **Query Parameters**: `pincode`, `district`, `state`.
- **Response**: List of matching CHCs.

### GET / PUT / PATCH / DELETE /api/v1/chc/{id}/
- **Description**: Retrieve, update, or delete a specific CHC.
- **Authentication**: Required (Authenticated User).
- **Permissions**: Typically restricted to the CHC's admin or Govt admin.

## 5. Machines

### GET /api/v1/machines/public/
- **Description**: List all machines available for public viewing.
- **Authentication**: Public.
- **Query Parameters**: `chc` (CHC ID), `machine_type`, `status`, `search` (name).
- **Response**: List of machines with availability status.

### GET /api/v1/machines/public/{id}/
- **Description**: Get detailed information about a specific machine.
- **Authentication**: Public.
- **Response**: Machine specifications, status, and CHC details.

### GET /api/v1/machines/
- **Description**: List machines for administrative purposes.
- **Authentication**: Required (CHC Admin sees their own, Govt Admin sees all).
- **Response**: Detailed machine list including maintenance info.

### POST /api/v1/machines/
- **Description**: Add a new machine to the CHC inventory.
- **Authentication**: Required (CHC Admin).
- **Body Parameters**: `machine_code`, `machine_name`, `machine_type`, `purchase_year`, `funding_source`, `status`.

### GET / PUT / PATCH / DELETE /api/v1/machines/{id}/
- **Description**: Manage a specific machine (Update status, maintenance info, etc.).
- **Authentication**: Required (CHC Admin of the machine's CHC).

## 6. Usage

### GET /api/v1/usage/
- **Description**: View history of machine usage records.
- **Authentication**: Required (CHC Admin sees their own, Govt Admin sees all).
- **Response**: Log of usage entries including farmer details and duration.

### POST /api/v1/usage/
- **Description**: Record a new machine usage entry after a booking is completed.
- **Authentication**: Required (CHC Admin).
- **Body Parameters**:
  - `machine`, `booking` (optional).
  - `farmer_name`, `usage_date`, `start_time`, `end_time`.
  - `start_meter_reading`, `end_meter_reading`.
  - `gps_lat`, `gps_lng`.
  - `residue_managed`, `area_covered`.
- **Response**: Created usage record.

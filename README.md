# Crop Residue Management (CRM) Backend

This is the backend for the Crop Residue Management (CRM) platform, built with Django and Django REST Framework.

## Setup Instructions

1.  **Clone the repository** (if applicable) or navigate to the project directory.

2.  **Create a virtual environment** (recommended):
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Linux/Mac
    venv\Scripts\activate     # On Windows
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Apply migrations**:
    ```bash
    python manage.py migrate
    ```

5.  **Create a Superuser (Government Admin)**:
    ```bash
    python manage.py createsuperuser
    ```

6.  **Run the server**:
    ```bash
    python manage.py runserver
    ```

## API Documentation

The API Documentation is available via Swagger UI:

-   **Swagger UI**: [http://127.0.0.1:8000/swagger/](http://127.0.0.1:8000/swagger/)
-   **Redoc**: [http://127.0.0.1:8000/redoc/](http://127.0.0.1:8000/redoc/)

## Key Usage Flows

1.  **Authentication**:
    -   Register as a CHC Admin via `/api/v1/auth/register/` (or create via admin panel).
    -   Login via `/api/v1/auth/login/` to get JWT tokens.
    -   Use the `access` token in the `Authorization: Bearer <token>` header for protected endpoints.

2.  **CHC Management**:
    -   Create CHC (Admin only).
    -   Add Machines to CHC.

3.  **Public Access**:
    -   Search for CHCs by pincode `/api/v1/chc/public/search/?pincode=123456`.
    -   View machine availability.
    -   Submit booking requests.

4.  **Admin Operations**:
    -   Approve/Reject bookings.
    -   Record machine usage.
    -   View dashboards.

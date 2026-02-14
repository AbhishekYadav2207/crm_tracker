# Setting up PostgreSQL for CRM Project

## Step 1: Install PostgreSQL and pgAdmin 4
Ensure you have PostgreSQL installed on your machine. The typical installation includes pgAdmin 4.

## Step 2: Create Database in pgAdmin 4

1.  Open **pgAdmin 4** and connect to your server (usually localhost:5432).
2.  Right-click on **Databases** > **Create** > **Database...**.
3.  Enter the database name: `crm_db`.
4.  Click **Save**.

## Step 3: Create a Database User (Optional but Recommended)

1.  Right-click on **Login/Group Roles** > **Create** > **Login/Group Role...**.
2.  **General** tab: Name = `crm_user`.
3.  **Definition** tab: Password = `password123` (or your preferred password).
4.  **Privileges** tab: Ensure "Can login?" is Yes.
5.  Click **Save**.
6.  Go back to your `crm_db` database, right-click > **Properties**. Change the **Owner** to `crm_user` if desired, or grant privileges.

## Step 4: Configure Django Project

1.  Open `crm_backend/settings.py`.
2.  Locate the `DATABASES` setting.
3.  Update it to use PostgreSQL:

    ```python
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': 'crm_db',
            'USER': 'postgres', # or 'crm_user'
            'PASSWORD': 'your_password',
            'HOST': 'localhost',
            'PORT': '5432',
        }
    }
    ```

    *Tip: It is best practice to use environment variables for sensitive info.*

## Step 5: Migrate Data

Since you are switching databases, you need to apply migrations again to create the schema in PostgreSQL.

```bash
python manage.py migrate
```

## Step 6: Create Superuser

```bash
python manage.py createsuperuser
```

## Step 7: Run Server

```bash
python manage.py runserver
```

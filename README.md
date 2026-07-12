# AssetFlow — Enterprise Asset & Resource Management System

AssetFlow is a premium, dark-themed Enterprise Asset & Resource Management System built using Django 6.0 and Tailwind CSS. It manages the full lifecycle of organization assets, handles department allocations, blocks double bookings of shared resources, coordinates maintenance requests, and organizes compliance audits.

---

## Recent Enhancements & Modernizations

Since the initial baseline, the application has been updated with the following enterprise-grade enhancements:

1. **Standardized Premium UI Layout**:
   - Standardized a unified sidebar template inclusion at [sidebar.html](file:///c:/Users/Vikas%20Gurram/Desktop/assetflow/assetflow/core/templates/core/includes/sidebar.html).
   - Cleaned up redundant navigation links across 15+ templates and replaced them with a single source of truth, removing over 1,000 redundant lines of HTML.
   - Fixed global layout wrappers by standardizing a `260px` canvas offset for content blocks in [base.html](file:///c:/Users/Vikas%20Gurram/Desktop/assetflow/assetflow/core/templates/core/base.html).

2. **Unified Form & Input Styling**:
   - Customized input fields, select dropdowns, labels, buttons, and checkboxes globally in the base layout (`base.html`). All forms (such as new department/category forms, resource booking, and user role promotions) now match the dark theme natively.

3. **Enterprise Test Suite**:
   - Implemented 12 comprehensive unit and integration tests inside [tests.py](file:///c:/Users/Vikas%20Gurram/Desktop/assetflow/assetflow/core/tests.py) covering RBAC view gates, double allocation blockers, overlapping booking time-slot checks, maintenance lifecycle state transitions, and audit cycle closure lost-status conversions.

4. **Security Hardening**:
   - Settings are secured via environment variables using python-dotenv.
   - Enforced strict server-side checks for signups: all public creations are forced to the `EMPLOYEE` role. Role promotion is restricted to the Administrator-only `/promote/` view.

---

## Setup & Running the Application

### 1. Setup and Activate Virtual Environment
```powershell
# Windows PowerShell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 2. Install Dependencies & Migrate
```powershell
pip install -r requirements.txt
python manage.py migrate
```

### 3. Seed Demo Data
Populates default assets, users, departments, and categories:
```powershell
python manage.py seed_demo
```

### 4. Run the Automated Tests
```powershell
python manage.py test
```

### 5. Launch the Development Server
```powershell
python manage.py runserver
```

---

## Role-Based Access Credentials (Demo Users)

All seeded demo accounts have password `pass1234` except `admin`.

| Username | Role | Purpose |
|---|---|---|
| `admin` / `admin1234` | Admin | Can manage organization setup, categories, and promote roles. |
| `asset_mgr1` | Asset Manager | Can register assets, allocate them, and approve maintenance. |
| `dept_head1` | Department Head | Can approve transfer requests. |
| `priya` | Employee | Standard employee holding the default laptop allocation. |
| `raj` | Employee | Standard employee with an overdue allocation (for overdue panel testing). |

---

## Crucial Business Rules (Implemented in `core/models.py`)

- **Double Allocation Protection**: Enforced inside `Allocation.create_for()` (raises `ValidationError` with details on who currently holds the asset).
- **Time Slot Overlap Protection**: Enforced inside `Booking.create_for()`. Checks `(start_time < existing.end) AND (end_time > existing.start)` to block overlapping bookings.
- **Maintenance State Flip**: Enforced inside `MaintenanceRequest.approve()`. Flipping a ticket to approved moves the asset status to `UNDER_MAINTENANCE` automatically.
- **Audit Deficiencies**: Enforced inside `AuditCycle.close()`. Closing an audit automatically sets all `MISSING` items to `LOST` in the asset directory.

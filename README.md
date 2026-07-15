# AssetFlow — Enterprise Asset & Resource Management System

![Django](https://img.shields.io/badge/Django-6.0-092E20?logo=django&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.x-3776AB?logo=python&logoColor=white)
![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-Dark_Theme-38BDF8?logo=tailwindcss&logoColor=white)
![Odoo Hackathon 2026](https://img.shields.io/badge/Odoo_Hackathon-2026-714B67)
![Tests](https://img.shields.io/badge/tests-12_passing-brightgreen)

AssetFlow is a premium, dark-themed **Enterprise Asset & Resource Management System** built on Django 6.0 and Tailwind CSS. It manages the full lifecycle of organizational assets — registration, department allocation, shared-resource booking, maintenance workflows, and compliance audits — with strict role-based access control.

Built for **Odoo Hackathon 2026**, problem statement: *AssetFlow — Enterprise Asset & Resource Management System*.

---

## 🎯 Problem Statement & Vision

Organizations that track equipment, furniture, vehicles, and shared spaces on spreadsheets and paper logs lose visibility into who holds what, where it is, and its condition. AssetFlow replaces that manual process with a centralized platform that digitizes the entire asset lifecycle — from registration and department allocation to shared-resource booking, maintenance approvals, and periodic compliance audits — while staying industry-agnostic (offices, schools, hospitals, factories, agencies) and out of purchasing/invoicing/accounting territory.

## ✨ Key Features

All 10 screens from the official problem statement are implemented, routed through `core/urls.py`:

| # | Screen | Nav Label | Status |
|---|---|---|---|
| 1 | Login / Signup | — | ✅ `signup/`, `login/`, `logout/` — public signup is hard-locked to `EMPLOYEE` server-side |
| 2 | Dashboard | Dashboard | ✅ role-aware home screen |
| 3 | Organization Setup | Organization | ✅ departments, categories, employee promotion (admin-only) |
| 4 | Asset Registration & Directory | Assets | ✅ directory, registration, edit, bulk retire |
| 5 | Asset Allocation & Transfer | Allocation | ✅ allocate, transfer request/approve/reject, return |
| 6 | Resource Booking | Bookings | ✅ create/cancel with overlap validation |
| 7 | Maintenance Management | Maintenance | ✅ full request → approve/reject → assign → in-progress → resolve lifecycle |
| 8 | Asset Audit | Audits | ✅ cycle creation, item marking, close-out |
| 9 | Reports & Analytics | Reports | ✅ `reports/` + CSV export |
| 10 | Activity Logs & Notifications | Activity Log / Notifications | ✅ per-user notification feed + system-wide activity log |

## 🖥 Screenshots

_Add 3–4 screenshots of the dashboard, booking calendar, and maintenance workflow here — dark-theme UI screenshots are one of the fastest ways to stand out in a hackathon README._

```
![Dashboard](docs/screenshots/dashboard.png)![Uploading Login.png…]()

![Resource Booking](docs/screenshots/booking.png)
```

## 🧱 Recent Enhancements & Modernizations

Since the initial baseline, the application has been updated with the following enterprise-grade enhancements:

1. **Standardized Premium UI Layout**
   - Unified sidebar template inclusion at [`sidebar.html`](core/templates/core/includes/sidebar.html).
   - Removed 1,000+ redundant lines of duplicated navigation HTML across 15+ templates in favor of one source of truth.
   - Standardized a 260px canvas offset for content blocks in [`base.html`](core/templates/core/base.html).

2. **Unified Form & Input Styling**
   - Inputs, selects, labels, buttons, and checkboxes are styled globally in `base.html`. All forms — department/category creation, resource booking, role promotion — match the dark theme natively.

3. **Enterprise Test Suite**
   - 12 unit and integration tests in [`tests.py`](core/tests.py) covering RBAC view gates, double-allocation blockers, overlapping booking checks, maintenance lifecycle transitions, and audit-cycle closure/lost-status conversion.

4. **Security Hardening**
   - Settings loaded from environment variables via `python-dotenv`.
   - Public signups are hard-locked to `Role.EMPLOYEE` server-side regardless of what the form submits; role changes only happen through the admin-gated `promote_employee` view.

## 🏗 Tech Stack

| Layer | Technology |
|---|---|
| Backend | Django 6.0, Python |
| Frontend | Tailwind CSS (dark theme, unified in `base.html`) |
| Database | SQLite |
| Config | python-dotenv |
| Testing | Django `TestCase` (12 tests) |

## ⚙️ Setup & Running the Application

### 0. Clone the Repository
```bash
git clone https://github.com/vikasgurram26/AssetFlow-Enterprise-Asset-Resource-Management-System.git
cd AssetFlow-Enterprise-Asset-Resource-Management-System
```

### 1. Setup and Activate Virtual Environment
```powershell
# Windows PowerShell
python -m venv venv
.\venv\Scripts\Activate.ps1
```
```bash
# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 2. Configure Environment
Create a `.env` file at the project root (loaded via `python-dotenv`):
```
SECRET_KEY=your-secret-key
DEBUG=True
```

### 3. Install Dependencies & Migrate
```bash
pip install -r requirements.txt
python manage.py migrate
```

### 4. Seed Demo Data
Populates default assets, users, departments, and categories:
```bash
python manage.py seed_demo
```

### 5. Run the Automated Tests
```bash
python manage.py test
```

### 6. Launch the Development Server
```bash
python manage.py runserver
```
Visit `http://127.0.0.1:8000/`.

## 🔑 Role-Based Access Credentials (Demo Users)

All seeded demo accounts use password `pass1234` except `admin`.

| Username | Role | Purpose |
|---|---|---|
| `admin` / `admin1234` | Admin | Manages organization setup, categories, and promotes roles. |
| `asset_mgr1` | Asset Manager | Registers assets, allocates them, approves maintenance. |
| `dept_head1` | Department Head | Approves transfer requests. |
| `priya` | Employee | Standard employee holding the default laptop allocation. |
| `raj` | Employee | Standard employee with an overdue allocation (for overdue panel testing). |

## 📐 Crucial Business Rules

Implemented in `core/models.py`:

- **Double Allocation Protection** — `Allocation.create_for()` raises `ValidationError` naming the current holder (employee or department) and directs the caller to Transfer Request instead of allowing a second allocation.
- **Transfer Workflow** — `TransferRequest.approve()` atomically closes the current allocation (`mark_returned()`) and opens a fresh `Allocation` for the target employee/department, so allocation history updates automatically rather than being overwritten.
- **Time Slot Overlap Protection** — `Booking.create_for()` checks `start_time < existing.end AND end_time > existing.start` against active bookings for the same asset. Booking status (Upcoming/Ongoing/Completed/Cancelled) is a **computed property**, not a stored field — it's derived live from `start_time`/`end_time` vs `now()`, so it can't drift out of sync.
- **Maintenance Lifecycle** — `MaintenanceRequest` moves through `Pending → Approved → Technician Assigned → In Progress → Resolved` (with a `Reject` branch off Pending), each transition guarded by its own method (`approve()`, `assign_technician()`, `start_progress()`, `resolve()`). The asset flips to `UNDER_MAINTENANCE` on approval and back to `AVAILABLE` on resolution.
- **Audit Deficiencies** — `AuditCycle.ensure_items()` idempotently creates one `AuditItem` per in-scope asset (filtered by department/location, excluding disposed assets). Closing the cycle (`close()`) converts any `MISSING` item's asset status to `LOST` and locks the cycle.
- **Notifications & Activity Log** — every state-changing action routes through a single `notify()` helper (`Notification` model) and `log_activity()` (`ActivityLog` model), rather than being scattered across views — keeping "what triggers a notification" answerable from one function.
- **Asset Tagging** — `asset_tag` auto-generates as `AF-0001`, `AF-0002`, … on first save if not supplied.

## 🧠 Notable Implementation Detail

Django resolves `urlpatterns` in list order. The literal maintenance sub-action paths (`/assign/`, `/start/`, `/resolve/`) are declared **before** the `<str:decision>` wildcard used for approve/reject in `core/urls.py` — otherwise Django would match `"assign"`/`"start"` as a `decision` string and silently misroute those requests into the reject branch. Caught via end-to-end testing.

## 📌 Remaining Before Submission

- [ ] Screenshots and a demo video walkthrough
- [ ] Fill in the remaining team roster
- [ ] Verify default branch name if adding absolute GitHub links elsewhere

---

Built for **Odoo Hackathon 2026**.

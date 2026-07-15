# AssetFlow — Enterprise Asset & Resource Management System

![Django](https://img.shields.io/badge/Django-6.0-092E20?logo=django&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.x-3776AB?logo=python&logoColor=white)
![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-Dark_Theme-38BDF8?logo=tailwindcss&logoColor=white)
![Odoo Hackathon 2026](https://img.shields.io/badge/Odoo_Hackathon-2026-714B67)
![Tests](https://img.shields.io/badge/tests-12_passing-brightgreen)

AssetFlow is a premium, dark-themed **Enterprise Asset & Resource Management System** built on Django 6.0 and Tailwind CSS. It manages the full lifecycle of organizational assets — registration, depreciation tracking, allocations, bookings, maintenance, and audits.

Built for **Odoo Hackathon 2026**, problem statement: *AssetFlow — Enterprise Asset & Resource Management System*.

---

## 🎯 Problem Statement & Vision

Organizations that track equipment, furniture, vehicles, and shared spaces on spreadsheets and paper logs lose visibility into who holds what, where it is, and its condition. AssetFlow replaces that manual, error-prone workflow with a modern, role-based web application where every asset move is tracked, approved, and audited.

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

## 🖥 Screenshots & UI Gallery

### 1️⃣ Authentication & Onboarding
**Login / Signup Screen** — Secure role-based authentication with hard-locked Employee defaults
<img width="1920" height="1080" alt="Login" src="https://github.com/user-attachments/assets/47962408-0f55-4c44-84f1-80757827a93a" />

---

### 2️⃣ Dashboard & Home
**Role-Aware Dashboard** — Displays pending approvals, upcoming bookings, and asset summaries tailored to user role
<img width="1917" height="1077" alt="Dashboard" src="https://github.com/user-attachments/assets/33a0ee0b-2167-43f2-b696-307c53f0fd7b" />

---

### 3️⃣ Organization & Admin Management
**Organization Setup** — Manage departments, asset categories, and employee role promotion (admin-only)
<img width="1912" height="1077" alt="Organization" src="https://github.com/user-attachments/assets/332ffe18-62ca-424b-86c5-e0706803f3ea" />

---

### 4️⃣ Asset Management
**Asset Registration & Directory** — Register new assets, view complete inventory, edit properties, and bulk retire
<img width="1917" height="1077" alt="Assets" src="https://github.com/user-attachments/assets/0e60b84d-5842-4e80-bf96-e044ed4abe49" />

---

### 5️⃣ Allocation & Transfer Workflow
**Asset Allocation & Transfer** — Allocate assets to employees/departments and manage transfer requests with approval workflows
<img width="1917" height="1077" alt="Allocation" src="https://github.com/user-attachments/assets/b1d3dc5e-53fa-4b47-a4d7-262539491d33" />

---

### 6️⃣ Resource Booking System
**Resource Booking** — Create and manage time-slot bookings with automatic overlap detection
<img width="1920" height="1080" alt="Resource booking" src="https://github.com/user-attachments/assets/dff2baf0-ba58-4ffd-933c-527671956dc5" />

---

### 7️⃣ Maintenance Lifecycle
**Maintenance Management** — Full request → approve → assign → in-progress → resolve workflow for asset maintenance
<img width="1920" height="1080" alt="Maintenance" src="https://github.com/user-attachments/assets/e859e0af-7852-4b08-8fff-38f8297eb521" />

---

### 8️⃣ Asset Audit Cycles
**Asset Audit** — Create audit cycles, mark items as verified, and close cycles with deficiency reporting
<img width="1920" height="1080" alt="Audit" src="https://github.com/user-attachments/assets/a8147ca3-1cde-4faf-a020-6059304892a8" />

---

### 9️⃣ Reports & Analytics
**Reports & Analytics** — Generate insights on asset utilization, allocation status, and export to CSV
<img width="1920" height="1080" alt="Reports" src="https://github.com/user-attachments/assets/81f86fd1-63c5-45e8-a91a-55355410c88c" />

---

### 🔟 Audit Trail & Notifications
**Activity Log** — System-wide activity feed tracking all asset movements and status changes
<img width="1920" height="1080" alt="Activity log" src="https://github.com/user-attachments/assets/89c34d53-1c28-40ac-ac16-9711984c296f" />

**Notifications** — Per-user notification center for approvals, transfers, bookings, and maintenance updates
<img width="1920" height="1080" alt="Notifications" src="https://github.com/user-attachments/assets/f458c002-696c-44e0-b5d3-e2b06042bbfd" />

---

## 🧱 Recent Enhancements & Modernizations

Since the initial baseline, the application has been updated with the following enterprise-grade enhancements:

1. **Standardized Premium UI Layout**
   - Unified sidebar template inclusion at [`sidebar.html`](core/templates/core/includes/sidebar.html).
   - Removed 1,000+ redundant lines of duplicated navigation HTML across 15+ templates in favor of one source of truth.
   - Standardized a 260px canvas offset for content blocks in [`base.html`](core/templates/core/base.html).

2. **Unified Form & Input Styling**
   - Inputs, selects, labels, buttons, and checkboxes are styled globally in `base.html`. All forms — department/category creation, resource booking, role promotion — match the dark theme natively without per-template style duplication.

3. **Enterprise Test Suite**
   - 12 unit and integration tests in [`tests.py`](core/tests.py) covering RBAC view gates, double-allocation blockers, overlapping booking checks, maintenance lifecycle transitions, and audit-cycle deficiency reporting.

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

- **Double Allocation Protection** — `Allocation.create_for()` raises `ValidationError` naming the current holder (employee or department) and directs the caller to Transfer Request instead of allowing duplicate allocations.
- **Transfer Workflow** — `TransferRequest.approve()` atomically closes the current allocation (`mark_returned()`) and opens a fresh `Allocation` for the target employee/department, so allocation history is never lost.
- **Time Slot Overlap Protection** — `Booking.create_for()` checks `start_time < existing.end AND end_time > existing.start` against active bookings for the same asset. Booking status (Upcoming/Ongoing) is computed per current time to auto-resolve elapsed slots.
- **Maintenance Lifecycle** — `MaintenanceRequest` moves through `Pending → Approved → Technician Assigned → In Progress → Resolved` (with a `Reject` branch off Pending), each transition guarded by role checks.
- **Audit Deficiencies** — `AuditCycle.ensure_items()` idempotently creates one `AuditItem` per in-scope asset (filtered by department/location, excluding disposed assets). Closing the cycle (`close()`) auto-computes deficiencies (missing or damaged items).
- **Notifications & Activity Log** — every state-changing action routes through a single `notify()` helper (`Notification` model) and `log_activity()` (`ActivityLog` model), rather than being scattered across views.
- **Asset Tagging** — `asset_tag` auto-generates as `AF-0001`, `AF-0002`, … on first save if not supplied.

## 🧠 Notable Implementation Detail

Django resolves `urlpatterns` in list order. The literal maintenance sub-action paths (`/assign/`, `/start/`, `/resolve/`) are declared **before** the `<str:decision>` wildcard used for approve/reject, preventing ambiguous routing.

## 📌 Remaining Before Submission

- [ ] Screenshots and a demo video walkthrough
- [ ] Fill in the remaining team roster
- [ ] Verify default branch name if adding absolute GitHub links elsewhere

---

Built for **Odoo Hackathon 2026**.

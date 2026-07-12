# AssetFlow Enterprise Asset & Resource Management System

## 1. Cover Page

| Item | Details |
|---|---|
| Project name | AssetFlow Enterprise Asset & Resource Management System |
| Application version | Not declared in the repository |
| Framework baseline | Django 6.0.7 |
| Document version | 1.0 |
| Document date | 12 July 2026 |
| Team name | Not declared in the repository |
| Authors | Not declared in the repository |

> This manual is based on the implemented Django application, its templates, models, routes, tests, and configuration. It does not describe planned capabilities as if they exist. Where repository metadata such as the team name, authors, or a product release version is absent, that fact is recorded rather than guessed.

---

## 2. Table of Contents

1. Cover Page

2. Table of Contents

3. Introduction

4. System Overview

5. User Roles

6. System Requirements

7. Getting Started

8. Navigation Guide

9. Module Documentation

10. Complete User Workflows

11. Dashboard Explanation

12. Forms

13. Reports & Analytics

14. Notifications

15. Frequently Asked Questions

16. Troubleshooting Guide

17. Limitations

18. Best Practices

19. Glossary

20. Appendix

---

## 3. Introduction

### Purpose

AssetFlow is a server-rendered web application for maintaining an enterprise asset register and operating related workflows. It records assets, departments, asset categories, allocations, transfers, time-slot bookings, maintenance requests, physical audit cycles, user notifications, and selected activity events.

### Target users

The implemented roles support ordinary employees, department heads, asset managers, and administrators. Employees can use shared-resource booking and request workflows. Department heads can additionally decide transfer requests. Asset managers manage the operational asset, maintenance, and audit workflows. Administrators manage organization setup as well as all asset-manager capabilities.

### Scope

The application covers:

- Account registration and sign-in.
- Role-based access to custom screens and workflow actions.
- Department and asset-category setup.
- Asset registration, update, search, filtering, allocation history, return, and transfer requests.
- Bookings of assets marked as bookable.
- Maintenance request lifecycle management.
- Scoped audit cycles and item verification.
- Dashboard indicators, reports, CSV asset export, notifications, and activity logs.

The application does not implement a public REST/JSON API, password-reset flow, asset attachments, automatic report scheduling, QR scanning, or a production deployment configuration.

### Key objectives

- Keep a structured register with unique asset tags and serial numbers.
- Prevent normal double allocation and overlapping active bookings.
- Route transfers and maintenance through approval states.
- Make physical audit discrepancies visible and mark missing assets as Lost when an audit is closed.
- Keep a lightweight, role-aware operational record.

---

## 4. System Overview

AssetFlow is a single Django project with one application, core. Django views render HTML templates and use a SQLite database. Most workflow rules are implemented in model methods, rather than only in page logic; this is important because the same rules apply wherever those methods are used.

### Core modules

| Module | Major capabilities |
|---|---|
| Authentication and RBAC | Sign-up, sign-in, sign-out, four application roles, role-gated actions |
| Organization | Departments, department hierarchy, department heads, asset categories, employee directory |
| Asset Registry | Register, edit, find, filter, inspect, and track asset history |
| Allocation and Transfer | Allocate, return, request a transfer, approve or reject a transfer |
| Booking | Reserve bookable assets by date and time; detect overlaps; cancel bookings |
| Maintenance | Raise, approve, reject, assign, start, and resolve maintenance requests |
| Audit | Create scoped cycles, assign auditors, mark items, review discrepancies, and close cycles |
| Oversight | Dashboard, reports, CSV export, notifications, and activity log |

### Major capabilities

Assets have a lifecycle status of Available, Allocated, Reserved, Under Maintenance, Lost, Retired, or Disposed. The implemented automated transitions are:

| Event | Result |
|---|---|
| Successful direct allocation | Asset becomes Allocated |
| Return | Allocation becomes Returned; asset becomes Available |
| Approved transfer | Existing allocation is returned; a new allocation is created for the destination |
| Approved maintenance request | Asset becomes Under Maintenance |
| Resolved maintenance request | Asset becomes Available |
| Closed audit with an item marked Missing | Asset becomes Lost |

Reserved, Retired, and Disposed can be selected when an authorized user edits an asset, but no dedicated custom workflow automatically sets those statuses. Booking an asset does not set its asset status to Reserved.

---

## 5. User Roles

Every custom role check accepts a Django superuser as well. A custom Admin role is not automatically the same thing as Django staff access to the separate Django administration site.

| Role | Responsibilities and accessible features | Restrictions |
|---|---|---|
| Employee | Can sign in, view the dashboard, organization directory, asset directory and asset details; request transfers; create bookings; raise maintenance requests; view maintenance, audit, reports, notifications, and activity-log screens. Can mark audit items only when assigned as an auditor. Can cancel a booking that they created. | Cannot register/edit/allocate/return assets; cannot manage organization data; cannot approve transfers or maintenance; cannot create/close audits unless role changes. |
| Department Head | All Employee capabilities. Can approve or reject requested transfers. Can be selected as a department head. | Cannot manage departments/categories/users, register/edit/allocate/return assets, approve maintenance, or create/close audits. Booking cancellation is still limited to their own bookings. |
| Asset Manager | All Employee capabilities. Can register and edit assets, allocate and return assets, approve/reject transfers, cancel any permitted booking, approve/reject maintenance, assign a technician, start work, resolve work, create audit cycles, close audit cycles, and mark audit items. | Cannot create or edit departments/categories or assign roles in the custom Organization screen. |
| Admin | All Asset Manager capabilities, plus create/edit departments, create/edit asset categories, and change an employee between Employee, Department Head, and Asset Manager using the Employee Directory. | The custom role-assignment form cannot grant the Admin role. It also does not set Django is_staff, so access to the separate Django admin site still requires the Django staff permission. |

### Role and account rules

- Public registration always creates an Employee account. The submitted request cannot choose a different role.
- An administrator may change a user to Employee, Department Head, or Asset Manager. The user may be assigned a department in the same action.
- The user record has Active and Inactive values, but the custom sign-in and permission decorators do not block an Inactive user. Active status is used to limit the employee and department choices in allocation and transfer forms.
- The Organization screen is viewable by any signed-in user; its create, edit, and role-assignment controls are shown only to an Admin and are also server-side protected.
- Some navigation links are visible even when the current user cannot perform the action. The destination action is still checked on the server and redirects an unauthorized user to the dashboard with “You don't have permission to do that.”

---

## 6. System Requirements

### Supported environment

The repository does not declare a browser-support matrix or minimum hardware specification. The following are practical requirements based on the implemented interface:

| Area | Requirement or recommendation |
|---|---|
| Browser | A current JavaScript-enabled desktop browser. The UI uses modern CSS, JavaScript, Tailwind CSS, and fixed multi-pane desktop layouts. |
| Display | A desktop-width display is recommended; many screens reserve a 260-pixel sidebar and show dense tables or multiple columns. |
| Internet connection | Required for the intended styled experience because Tailwind CSS, Google fonts, Material Symbols, and some decorative avatar/product images are loaded from external CDNs or image hosts. |
| Application runtime | Python 3.x and the dependency listed in requirements.txt: Django 6.0.7. |
| Database | SQLite, stored in db.sqlite3 in the project root. No external database service is configured. |
| JavaScript | Required for timeline rendering, in-page filters, drawers, tabs, chart rendering, and several screen-level interactions. |

### Dependencies

- Django 6.0.7 is the only Python package listed by the project.
- Tailwind CSS is loaded at runtime from a CDN; it is not built locally.
- Google-hosted Inter and Material Symbols fonts are loaded by templates.
- There is no Node.js dependency, package manifest, REST framework, task queue, mail service, or file-storage configuration in the repository.

---

## 7. Getting Started

### Installation

From the project root, create an isolated environment, install the declared dependency, apply migrations, and start Django:

~~~powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
~~~

Open http://127.0.0.1:8000/ in a browser.

For a pre-populated demonstration environment, run the following after migration:

~~~powershell
python manage.py seed_demo
~~~

The seed command creates sample departments, categories, assets, an open audit cycle, a booking, and demonstration users. It is idempotent for the seeded records. Do not use the sample credentials in a production deployment.

The repository contains run.txt with platform startup instructions, but no run.bat or run.sh file is present in the project tree.

### Demo accounts

| Username | Role | Seeded password |
|---|---|---|
| admin | Admin and Django superuser | admin1234 |
| dept_head1 | Department Head | pass1234 |
| asset_mgr1 | Asset Manager | pass1234 |
| priya | Employee | pass1234 |
| raj | Employee | pass1234 |

### Login process

1. Open the Sign in page.
2. Enter Username and Password.
3. Select **Sign In**.
4. A valid account is redirected to the dashboard. Invalid credentials display **Invalid username or password.**
5. Use the logout icon at the bottom of the sidebar to end the session.

### Registration process

1. On the Sign in page, select **Create Account**.
2. Enter first name, last name, username, email address, password, and password confirmation.
3. Select **Create Account**.
4. The system creates the account with the Employee role and signs the user in.
5. An administrator can later assign an elevated supported role from Organization → Employee Directory.

Registration uses Django password validation. The configured validators reject passwords that are too similar to user information, shorter than Django’s default minimum length of eight characters, common, or entirely numeric. Username uniqueness and valid email syntax are also checked.

### Password reset

Password reset, forgotten-password, email verification, and user self-service password change are **not implemented**. There is no password-reset link or route in the custom UI.

### First-time setup

For a blank database, use this sequence:

1. Create or sign in with a Django superuser/administrator.
2. Open **Organization** and add one or more asset categories. A category is required when registering an asset.
3. Add departments as needed, optionally select a department head and parent department, and set a department status.
4. Have users sign up; their accounts start as Employees.
5. Use Employee Directory → **Assign Role** to make eligible users Department Heads or Asset Managers.
6. Register assets, set their department/location/condition, and select **Bookable** for shared resources that may be reserved by time slot.

---

## 8. Navigation Guide

### Sidebar

The fixed sidebar provides Dashboard, Organization, Assets, Allocation, Booking, Maintenance, Audit, Reports, Activity Log, and Notifications. It also shows the signed-in user’s name and role, a notification count, a logout control, and a **Register Asset** shortcut. Access to protected actions remains role-checked even if a shortcut is visible.

### Dashboard

The dashboard is the default signed-in landing page. It offers a global asset search box, notification link, booking and maintenance shortcuts, KPI cards, overdue and upcoming return tables, a recent activity preview, and CSV export shortcut. See [Dashboard Explanation](#11-dashboard-explanation).

### Menus and navigation flow

The main operating flow is:

1. Set up categories and departments.
2. Register an asset.
3. Allocate it, return it, or request a transfer.
4. Mark shared resources bookable and use the Booking page for time slots.
5. Raise and process maintenance requests.
6. Create audit cycles to validate assets physically.
7. Review dashboard, reports, notifications, and activity events.

### Search and filters

| Screen | Implemented search/filter behavior |
|---|---|
| Dashboard | Search submits to Asset Directory and searches asset tag, name, or serial number. The placeholder mentions users/resources, but only asset fields are searched. |
| Asset Directory | Server-side keyword search by tag, name, or serial; server-side category/status filters; client-side department/location dropdown filters populated from currently displayed rows. |
| Organization | Client-side text search filters only the currently selected tab. |
| Allocation & Transfer | Client-side asset search and status chips for All, Available, Allocated, and Pending Request. |
| Booking | Server-side resource dropdown filters the booking log; date arrows only change the client-side timeline date. |
| Audit detail | Client-side text filter for audit item rows. |
| Notifications | Client-side All/Unread toggle. |
| Activity Log | Client-side All/Alerts/Approvals/Bookings categorization based on text in the description. |

### Notifications

The notification bell and Notifications page display only the signed-in user’s notification records. An unread count appears in the sidebar and on several page headers. A notification can be marked read individually; there is no “mark all read” action.

---

## 9. Module Documentation

### 9.1 Authentication and account registration

**Purpose.** Creates an Employee account or starts an authenticated session.

**Features and screens.** Sign in, Create Account, and logout. Screens: Sign in, Sign up, Dashboard.

**How to use.**

1. Register with the required identity and password fields, or sign in with existing credentials.
2. After registration, use the dashboard and ask an Admin for a supported elevated role when needed.
3. Use the sidebar logout control when finished.

**Inputs and validation.** Registration requires first name, last name, username, email, password, and matching confirmation. Django validates the password and unique username. Login requires nonblank username and password. The public form has no role input and server code forces Employee regardless of extra submitted data.

**Outputs and expected behavior.** A successful signup creates and logs in an Employee. A successful login redirects to Dashboard. Invalid login produces an error. No password recovery is available.

**Tips.** Use the seed command only for demonstration. Change seed passwords and development configuration before exposing an instance to other users.

### 9.2 Organization setup

**Purpose.** Maintains departments, categories, and the visible employee directory.

**Features and screens.** Organization has Departments, Asset Categories, and Employee Directory tabs, a client-side search, detail drawer, and Admin-only creation/editing controls.

**How to use.**

1. Open **Organization**.
2. In Departments, select **Add Department** (Admin) or edit a row. Enter a unique name, optional eligible head, optional parent, and status.
3. In Asset Categories, select **Add Category** (Admin) or edit a row. Enter a unique name, optional description, and optional warranty period in days.
4. In Employee Directory, select **Assign Role** (Admin), select Employee, Department Head, or Asset Manager, optionally select a department, then save.

**Inputs and validation.**

- Department: name is required and unique; head choices are limited to Department Heads and Admins; parent and status are available.
- Asset category: name is required and unique; description and warranty days are optional; warranty days must be a non-negative integer.
- Role assignment: a role selection is required; department is optional. Admin is not a selectable target role in this form.

**Business rules and restrictions.** Any signed-in user can view the data. Only Admin can create/edit departments/categories or change roles. There is no custom UI for deleting these records, editing a user’s Active/Inactive status, or creating a user except public signup.

**Error handling.** Invalid form data is displayed beside its field. Unauthorized operations return to the dashboard with a permission message.

### 9.3 Asset Registry

**Purpose.** Creates and maintains the master record for each asset.

**Features and screens.** Asset Directory, filters, client-side detail drawer, Register Asset, Edit Asset, and Asset Detail.

**How to use.**

1. An Asset Manager or Admin opens **Assets** and selects **Register Asset**.
2. Enter the asset details and save.
3. AssetFlow generates the asset tag on first save in AF-0001 format.
4. Search by asset tag, name, or serial number; select an asset row to inspect the drawer or open its full detail page.
5. Use **Edit Asset** to revise permitted fields.

**Inputs.** Name, category, serial number, acquisition date, acquisition cost, condition, location, bookable flag, department, and status. Category, name, serial number, acquisition date, acquisition cost, condition, and status are required by the model/form. Location and department are optional; Bookable is optional and defaults off.

**Validation and business rules.**

- Asset tags are unique and generated automatically when blank.
- Serial numbers are unique.
- An asset category cannot be removed while assets reference it because the relationship is protected.
- The system uses a max-plus-one tag generator. It is suitable for demonstration scale but can race if two new assets are saved at exactly the same time.

**Outputs and expected behavior.** Saving redirects to the asset detail page and records an activity event. Asset Detail shows metadata, up to 10 allocation records, and up to 10 maintenance requests for the asset.

**Tips.** Create categories before assets. Mark only genuinely shareable assets as Bookable. Use accurate location and department values because they drive audit scoping and report grouping.

### 9.4 Allocation, return, and transfer

**Purpose.** Records custody of an asset by an employee or department and manages custody changes.

**Features and screens.** Asset Detail contextual forms, Allocation & Transfer page, allocation history, return action, transfer queue, and approve/reject buttons.

**Direct allocation — how to use.**

1. Choose an Available asset.
2. An Asset Manager or Admin selects an active employee or active department and may enter an expected return date.
3. Submit **Allocate Asset**.
4. The system creates an active allocation, changes the asset to Allocated, and notifies the selected employee when one is supplied.

**Return — how to use.**

1. Open an Allocated asset.
2. An Asset Manager or Admin enters optional condition notes.
3. Select **Mark Returned**.
4. The active allocation is closed, the return timestamp is stored, and the asset becomes Available.

**Transfer — how to use.**

1. From Asset Detail or Allocation & Transfer, select a destination active employee or active department.
2. Submit the request; any signed-in user may request it.
3. A Department Head, Asset Manager, or Admin opens Allocation & Transfer and approves or rejects a Requested transfer.
4. Approval returns any current allocation, creates a new allocation for the destination, preserves allocation history, and keeps the asset Allocated. Rejection leaves the current allocation unchanged.

**Validation and error handling.**

- Direct allocation only succeeds when the asset status is Available.
- Allocating an already Allocated asset returns a message identifying the current holder and directs the user to Transfer Request.
- Assets in any other status cannot be allocated.
- A return fails if the allocation is already closed.
- A transfer can only be approved or rejected while its status is Requested.
- The standard form requires at least one destination. The Allocation & Transfer page adds browser-side validation requiring exactly one employee or department, but the server-side form does not reject both values when posted.

**Tips.** Use a transfer for a change in holder, not a return followed by a separate allocation. Enter an expected return date for temporary custody so the dashboard can identify overdue and upcoming returns.

### 9.5 Resource Booking

**Purpose.** Reserves a bookable asset for a time interval.

**Features and screens.** Book Resource form, resource dropdown, interactive daily timeline, booking history table, and cancellation action.

**How to use.**

1. Select **Booking** → **Book Resource**.
2. Select a bookable asset, start date/time, and end date/time.
3. Submit **Book**.
4. Return to Booking to see the log and timeline. Use the left/right arrows to render another day in the timeline.
5. For an Upcoming booking, select **Cancel** when the action is permitted.

**Inputs and validation.**

- Asset, start time, and end time are required.
- The selection list contains bookable assets except those marked Retired, Disposed, or Lost.
- End time must be after start time.
- A non-cancelled booking conflicts when its interval overlaps the requested interval. Adjacent bookings are allowed; for example, a request beginning exactly when another ends is valid.
- The model rejects an asset that is not marked Bookable.

**Outputs and expected behavior.** A successful booking creates a notification for the booker and an activity log entry. Booking status is calculated at display time as Upcoming, Ongoing, Completed, or Cancelled. The timeline displays non-cancelled bookings on the selected day, visually clamped to 08:00–18:00; bookings outside those hours remain in the history log but do not draw on the timeline.

**Restrictions and tips.** Any signed-in user can create a booking. The booking owner can cancel their booking; an Asset Manager or Admin can cancel any booking. The UI shows Cancel only for Upcoming records, although the server-side cancellation view does not independently enforce an Upcoming check. Always check the history table after submitting; there is no booking approval workflow.

### 9.6 Maintenance

**Purpose.** Records a reported asset issue and progresses it through an operational repair workflow.

**Features and screens.** Raise Maintenance Request form and Kanban-style Maintenance Board with Pending, Approved, Tech Assigned, In Progress, and Resolved columns. Rejected requests are displayed in the Resolved column with a Rejected status.

**How to use.**

1. Select **Maintenance** → **New Ticket**.
2. Select an eligible asset, describe the issue, choose Low, Medium, or High priority, and submit.
3. An Asset Manager or Admin approves or rejects a Pending request.
4. After approval, assign a technician by name.
5. Select **Start Progress** after a technician is assigned.
6. Select **Resolve Repair** when work is complete.

**Inputs and validation.**

- Asset and issue description are required; priority defaults to Medium.
- The request form excludes assets already Under Maintenance, Retired, Disposed, or Lost.
- Only a Pending request can be approved or rejected.
- A technician may be assigned only after approval.
- Work can start only after technician assignment.
- Resolution is permitted from Approved, Technician Assigned, or In Progress in the model; the board exposes the normal Resolve button in the In Progress column.

**Business rules and expected behavior.**

- Raising a request leaves the asset’s status unchanged.
- Approval changes the asset to Under Maintenance and notifies the requester.
- Rejection notifies the requester and does not change the asset.
- Resolution records a resolution timestamp, changes the asset to Available, and notifies the requester.
- The visible 50% progress bar on In Progress cards is decorative and not calculated from work data.

**Tips.** Describe a specific symptom and set the priority consistently. Do not expect file attachments, repair costs, technician accounts, maintenance dates, or service-level tracking; they are not present.

### 9.7 Audit cycles

**Purpose.** Creates a list of assets for physical verification and captures verification outcomes.

**Features and screens.** Audit Cycles list, Create Audit Cycle form, Audit Workspace, scope-driven item creation, client-side item filter, discrepancy report, progress indicator, and close action.

**How to use.**

1. An Asset Manager or Admin selects **Audit** → **Create Audit Cycle**.
2. Enter a cycle name, optional department and/or location scope, start/end dates, and optional auditors.
3. Save. The system creates one Pending audit item for each in-scope asset.
4. Open the cycle. An assigned auditor, Asset Manager, or Admin selects Verified, Missing, or Damaged for each item, optionally adds notes, and saves.
5. Review the Discrepancy Report for Missing and Damaged items.
6. An Asset Manager or Admin selects **Close Audit Cycle** and confirms.

**Scope and validation.**

- Only non-Disposed assets are included.
- Department scope matches the asset’s department exactly.
- Location scope matches when the asset location contains the entered text, case-insensitively.
- If both scopes are supplied, both must match. If neither is supplied, all non-Disposed assets are in scope.
- Name, start date, and end date are required. Scope and auditors are optional.
- No form validation checks that the end date is on/after the start date, that a scope exists, or that an auditor is selected.

**Business rules and expected behavior.**

- Loading an audit detail page calls an idempotent item-generation method. New in-scope assets can therefore be added to an open cycle if the detail page is subsequently opened.
- Marking Missing or Damaged creates a notification for every assigned auditor.
- Closing does not require every item to be marked.
- On close, every item marked Missing changes its asset to Lost. Damaged does not automatically change the asset status.
- The UI hides editing controls after a cycle is closed and marks it Closed. There is no dedicated discrepancy-resolution workflow.

**Tips.** Assign auditors at creation to give them marking rights. Use scope fields carefully because they directly control the generated work list. The visible **Scan Tag** button is present but has no implemented scanning action.

### 9.8 Dashboard

**Purpose.** Provides an at-a-glance operational overview.

**Features and screens.** KPI cards, overdue alert/table, recent activity preview, portfolio graphic, upcoming returns, and shortcuts. Detailed metric definitions appear in Section 11.

**Expected behavior.** All signed-in users see the same asset-wide KPIs, overdue returns, and recent activity records; these dashboard areas are not restricted to a user’s department or ownership. The notification preview is specific to the current user.

### 9.9 Reports and CSV export

**Purpose.** Provides aggregate asset and maintenance views plus a complete asset-register download.

**Features and screens.** Reports & Analytics screen, department and category charts, Most Maintained list, Idle Assets/Nearing Review list, and Export CSV.

**How to use.**

1. Open **Reports**.
2. Hover over chart points to see rendered values.
3. Select **Export CSV** to download assetflow_report.csv.

**Outputs.** CSV includes Tag, Name, Category, Status, Department, Location, Acquisition cost, Acquisition date, and Bookable for every asset. No report filters alter the export.

**Tips.** Read the report labels with the definitions in Section 13. Some visual labels are broader than the underlying calculation.

### 9.10 Notifications

**Purpose.** Presents workflow notices addressed to the current user.

**How to use.**

1. Select the bell or **Notifications** in the sidebar.
2. Use **All** or **Unread** to filter the currently loaded list in the browser.
3. Select **Mark as Read** on an unread notification.

**Expected behavior.** Marking a record read removes it from the unread count. Notification titles/icons are assigned by client-side keyword matching; the full stored message is the authoritative content. See Section 14 for exact triggers.

### 9.11 Activity Log

**Purpose.** Provides a lightweight operational history of explicitly logged actions.

**Features and screens.** The Activity Log page displays the 200 newest activity entries across the system. Client-side filters categorize text as Alerts, Approvals, or Bookings.

**Expected behavior and restrictions.** Every signed-in user can view the same log entries. It is not a complete immutable audit trail: only selected view actions create entries. Section 14 identifies what is and is not logged.

### 9.12 Django administration site

**Purpose.** Provides Django’s separate back-office at /admin/ for registered database models.

**Access.** This is not the custom AssetFlow interface. It requires a Django staff user, normally the seeded superuser. The registered models are User, Department, AssetCategory, Asset, Allocation, TransferRequest, Booking, MaintenanceRequest, AuditCycle, AuditItem, Notification, and ActivityLog.

**Use with care.** Direct administrative edits can bypass the normal custom-screen workflow sequence. The custom Admin role alone does not set Django is_staff when assigned through Organization.

---

## 10. Complete User Workflows

### 10.1 New user to active Employee

1. Open Create Account.
2. Submit valid identity and password fields.
3. The application creates an Employee, signs the person in, and redirects to Dashboard.
4. The Employee can view the directory, request transfers, book shared assets, and raise maintenance requests.

### 10.2 Administrator setup

1. Sign in as an account with the custom Admin role.
2. In Organization, create categories before registering assets.
3. Create departments and optionally set parent departments and eligible heads.
4. Ask users to sign up, then assign Department Head or Asset Manager roles as needed.
5. Register assets and assign their department, location, status, and bookable flag.

### 10.3 Register and allocate an asset

1. Asset Manager/Admin opens Assets → Register Asset.
2. Enter a unique serial number and required asset details.
3. Save; the system generates an AF tag and opens Asset Detail.
4. While the status is Available, select an active employee or department and optionally an expected return date.
5. Submit Allocate Asset.
6. The asset becomes Allocated; an employee recipient receives a notification.

### 10.4 Return an asset

1. Open the Allocated asset.
2. Confirm the current holder in the Release & Return panel.
3. Asset Manager/Admin enters optional condition notes.
4. Select Mark Returned.
5. The allocation is marked Returned and the asset becomes Available.

### 10.5 Transfer an asset

1. A signed-in user opens an asset and requests transfer to an active employee or department.
2. The request is stored as Requested.
3. Department Head, Asset Manager, or Admin opens Allocation & Transfer, selects the asset with the pending request, and approves or rejects it.
4. On approval, the old allocation is returned, a new allocation is created, and the destination employee is notified when applicable.
5. On rejection, the request is marked Rejected and the requester is notified.

### 10.6 Book a shared resource

1. Ensure the asset’s Bookable field is checked.
2. Any signed-in user opens Book Resource.
3. Select the resource and a valid start/end interval.
4. Submit.
5. If no non-cancelled interval overlaps, the booking is created and appears in the timeline/history log.
6. The booker or an Asset Manager/Admin can cancel according to the implemented access rule.

### 10.7 Process maintenance

1. Any signed-in user creates a ticket with asset, issue, and priority.
2. The card appears under Pending.
3. Asset Manager/Admin approves it; the asset becomes Under Maintenance.
4. Asset Manager/Admin assigns a technician.
5. Asset Manager/Admin starts progress.
6. Asset Manager/Admin resolves the ticket; the asset becomes Available.

### 10.8 Run an audit

1. Asset Manager/Admin creates a scoped audit cycle and optionally assigns auditors.
2. The system generates Pending items for matching non-Disposed assets.
3. Assigned auditor, Asset Manager, or Admin marks each item Verified, Missing, or Damaged and may add notes.
4. Review discrepancy items.
5. Asset Manager/Admin closes the cycle.
6. All Missing items change their associated asset to Lost; the cycle becomes Closed and auditors are notified.

### 10.9 Review oversight information

1. Use Dashboard for operational counts, overdue returns, upcoming returns, activity preview, and quick actions.
2. Open Reports for aggregate charts and CSV export.
3. Open Notifications to read workflow messages.
4. Open Activity Log to see the latest explicitly logged actions.

---

## 11. Dashboard Explanation

### KPI cards

| Card | Actual calculation |
|---|---|
| Available | Count of assets whose status is Available. |
| Allocated | Count of assets whose status is Allocated. |
| Maintenance Today | Count of maintenance requests in Approved, Technician Assigned, or In Progress. It is not filtered to today’s date despite the label. |
| Bookings Active | Count of non-cancelled bookings whose end time is now or later. It includes both Upcoming and Ongoing bookings. |
| Transfers Pending | Count of transfer requests with Requested status. |
| Returns Upcoming | Count of the displayed subset of active allocations with an expected return date today or later. The underlying list is limited to eight records, so the card is also capped by that display slice. |

The mini sparklines and bar illustrations in these cards are static decoration; they are not calculated from historical data.

### Alert and tables

| Widget | Meaning and action |
|---|---|
| Overdue banner | Appears when an active allocation has an expected return date earlier than today. **Review Now** scrolls to the overdue table. |
| Overdue Returns | All active allocations past their expected return date. Select a row to open the asset. |
| Recent Activity Log | Ten newest ActivityLog entries across the system. **View All** opens Activity Log. |
| Upcoming Returns | Up to eight active allocations with expected return date today or later; entries with no expected return date are excluded. Select a row to open the asset. |
| Unread notifications | Up to five unread notifications for the signed-in user are loaded by the view, though this standalone dashboard template does not display a dedicated notification-preview panel. The bell opens Notifications. |

### Portfolio Breakdown

The number in the centre is Available plus Allocated assets. The surrounding donut segments, the IT Equipment/Vehicles/Machinery/Facilities legend, and their percentages are hard-coded visual placeholders. They are not derived from categories or asset data and should not be used as an analytical report.

### Quick actions

- **Book Resource** opens the booking form.
- **Raise Request** opens maintenance request creation.
- **Register New Asset** opens asset registration; the server permits it only to Asset Managers/Admins.
- **Book Shared Resource** opens booking creation.
- **Raise Maintenance Ticket** opens maintenance creation.
- **Export CSV Report** downloads the complete asset export.

---

## 12. Forms

### Form reference

| Form | Required fields | Optional fields | Submission result |
|---|---|---|---|
| Sign up | First name, last name, username, email, password, password confirmation | None | Employee account is created and signed in. |
| Sign in | Username, password | None | Valid credentials open Dashboard. |
| Department | Name, status | Head, parent | Department is created or updated. |
| Asset category | Name | Description, warranty period days | Category is created or updated. |
| Assign Role | Role | Department | Target role/department are updated. |
| Asset | Name, category, serial number, acquisition date, acquisition cost, condition, status | Location, bookable flag, department | Asset is created/updated; new asset receives a tag. |
| Allocate | At least employee or department | Expected return date | Active allocation is created when the asset is Available. |
| Return | None | Condition notes | Allocation closes and asset becomes Available. |
| Transfer request | At least destination employee or department | None | Request becomes Requested. |
| Booking | Asset, start time, end time | None | Booking is created if eligible and non-overlapping. |
| Maintenance request | Asset, issue description, priority | None | Pending maintenance request is created. |
| Technician assignment | Technician name | None | Approved request becomes Technician Assigned. |
| Audit cycle | Name, start date, end date | Department scope, location scope, auditors | Cycle and in-scope items are created. |
| Audit item mark | Result | Notes | Item result and checked time are saved. |

### Validation and submission behavior

- Form errors are rendered beside fields on the templates that use Django form rendering. Model/business errors from workflows are shown as page messages or non-field errors.
- Department and category names must be unique.
- Warranty period accepts only a non-negative whole number.
- Acquisition cost is a decimal with up to 12 digits and 2 decimal places.
- Allocation/transfer selection lists contain only Active employees and Active departments. The model allows both fields if a crafted request sends both; the operational Transfer page’s JavaScript blocks that combination, but the basic Asset Detail form does not.
- Bookings must end after they start and may not overlap a non-cancelled booking for the same asset.
- Maintenance workflow actions are rejected when performed out of order.
- Audit result choices are Verified, Missing, and Damaged. Pending is the initial stored result and is not a selectable marking button.
- No implemented validator requires expected return dates, booking times, or audit dates to be in the future. No implemented audit validator compares start date with end date.

### Common messages

| Situation | Message or behavior |
|---|---|
| Invalid login | “Invalid username or password.” |
| Protected action | “You don't have permission to do that.” |
| Double allocation | Identifies the current holder and says to use Transfer Request instead. |
| Invalid booking interval | “End time must be after start time.” |
| Booking overlap | Identifies the existing booking interval that overlaps the request. |
| Maintenance out of sequence | Explains the required prior state, such as assigning a technician before starting work. |
| Repeat audit closure | “This audit cycle is already closed.” |
| Unauthorized audit marking | “You're not an auditor on this cycle.” |

---

## 13. Reports & Analytics

### Screen metrics

| Report widget | What it actually means |
|---|---|
| Total Registered Assets | Number of all assets, summed from category totals. |
| Avg Allocation Rate | Rounded percentage: assets with status Allocated divided by all registered assets. It is not an average over time. |
| Top Maintenance Count | Highest number of maintenance-request records for one asset. All request statuses are counted, not only resolved repairs. |
| Nearing Review | Number of entries in the displayed oldest-Available list, capped at ten. It is not based on a configurable retirement/review rule. |
| Asset Allocations by Department | Despite the label, plots the count of assets whose department field is set to each department. It does not count allocations and excludes assets with no department. |
| Category Breakdown: Total vs Allocated | For each category, shows total assets and the subset whose status is Allocated. |
| Most Maintained Assets | Up to ten asset tags with the greatest number of maintenance-request records. |
| Idle Assets (Nearing Review) | Up to ten Available assets ordered from oldest acquisition date. “Idle” and “Nearing Review” are display labels; no idle-duration or retirement threshold is calculated. |

### Export

**Export CSV** sends assetflow_report.csv to the browser. It exports the entire asset register and has no date, department, category, or status filter. There is no PDF export, scheduled report, report sharing, utilization trend, or booking heatmap feature.

---

## 14. Notifications

### Notification triggers

| Trigger | Recipient |
|---|---|
| Asset allocated to an employee | Allocated employee |
| Transfer approved | Destination employee, if a person rather than a department is selected |
| Transfer rejected | User who requested the transfer |
| Booking created | User who made the booking |
| Booking cancelled | User who made the booking |
| Maintenance approved, rejected, or resolved | User who raised the maintenance request |
| Audit item marked Missing or Damaged | Every auditor assigned to that audit cycle |
| Audit cycle closed | Every auditor assigned to that cycle |

No notification is created for a department-only allocation, because there is no recipient user. The application does not implement email, push, SMS, automatic overdue reminders, notifications for technician assignment/start, role assignment, or notification broadcasts.

### Activity-log coverage

The Activity Log is separate from notifications. It records selected actions: department create/update, role assignment, asset registration/update, allocation, transfer request and decision, return, booking creation, maintenance request creation/resolution, and audit cycle creation/closure.

It does not log every database change. In particular, category changes, booking cancellation, maintenance approval/rejection/assignment/start, audit item marking, notification reads, sign-in/sign-out, and sign-up do not create an ActivityLog entry in the implemented views.

---

## 15. Frequently Asked Questions

### Can a user choose Asset Manager or Admin during sign-up?

No. Sign-up always assigns Employee. An Admin may later assign Employee, Department Head, or Asset Manager. The custom role form cannot assign Admin.

### Why cannot I allocate an asset?

Only Asset Managers and Admins can allocate. The asset must also be Available. If it is already Allocated, use a transfer request or return it first.

### Can I allocate an asset to a department?

Yes. Select an active department. A department allocation has no individual recipient, so it does not create a user notification.

### Why was my booking rejected?

The selected asset may not be bookable, the end time may not be after the start time, or the interval overlaps an existing non-cancelled booking for the same asset.

### Can a booking be approved by a manager?

No. Booking is confirmed immediately when it passes validation. There is no booking approval state.

### Why is a maintenance asset unavailable?

Approval changes its status to Under Maintenance. Resolution changes it back to Available.

### What happens when an audit item is Missing?

It appears as a discrepancy immediately. Its asset becomes Lost only when the audit cycle is closed.

### Can I restore a Lost asset through the UI?

There is no dedicated restore workflow. An Asset Manager/Admin can edit the asset status in Asset Edit.

### Why does the dashboard portfolio chart not match my categories?

The portfolio donut legend and percentages are static display artwork. Use Reports for data-derived category totals.

### Is there a password-reset option?

No. It is not implemented.

---

## 16. Troubleshooting Guide

| Issue | Likely cause | Resolution |
|---|---|---|
| The application will not start | Virtual environment/dependency/migrations are missing | Activate the environment, run pip install -r requirements.txt, run python manage.py migrate, then runserver. |
| Styling or icons are missing | External Tailwind/font/CDN resources cannot load | Restore internet access or provide an approved local asset/build strategy; the repository currently expects external resources. |
| Sign in fails | Wrong username/password or account data | Verify credentials. The UI has no password-reset feature; a staff administrator must assist outside the custom flow. |
| I see an action but receive a permission error | Navigation can be visible while server access is restricted | Sign in with the required role or request a role assignment from an Admin. |
| No category is available for a new asset | Categories have not been created | Admin should add an asset category in Organization first. |
| Asset will not allocate | It is not Available, or no holder was selected | Return/transfer the current allocation as appropriate; choose at least an active employee or department. |
| Transfer cannot be approved | It is no longer Requested | Refresh the transfer list and check whether another decision already occurred. |
| Booking will not save | Invalid time order, overlap, or non-bookable asset | Choose a bookable asset, set end after start, and select a free interval. |
| A booking is not visible in the day grid | Its time is outside 08:00–18:00 or it is cancelled | Check the booking history table; use date arrows to select the correct day. |
| Maintenance action fails | Attempted workflow step is out of order | Approve first, assign technician, start progress, then resolve. |
| I cannot mark an audit item | You are neither assigned auditor nor Asset Manager/Admin | Ask an Asset Manager/Admin to add you as an auditor or perform the mark. |
| “Scan Tag” does nothing | No scan implementation is connected to that button | Search/filter the audit item manually; scanning is not implemented. |
| Report title appears inconsistent with data | Some labels are presentation labels | Use the exact metric definitions in Section 13. |

---

## 17. Limitations

The following limitations are present in the current codebase:

- No password-reset, password-change, email verification, MFA, email delivery, SSO, or external identity-provider integration.
- No public REST/JSON API; all application routes render HTML or perform form actions, except the CSV download.
- SQLite is the configured database; DEBUG is enabled and allowed hosts are unrestricted in the checked-in development settings. A secret key is present in source code and should not be reused in production.
- No environment variables are read by settings.py. A .env name is ignored by Git, but no environment-variable configuration mechanism is implemented.
- No uploaded asset photos, documents, maintenance attachments, media storage, or image-processing dependency. Some screens use externally hosted decorative images instead.
- Asset categories provide only a name, description, and optional generic warranty period; no dynamic category-specific field schema is implemented.
- No custom deletion actions for assets, departments, categories, users, bookings, transfers, maintenance requests, audits, notifications, or activity logs.
- No pagination is implemented for asset/booking/transfer/report data. Asset Directory shows pagination-looking buttons but they do not change pages.
- The Asset Directory selection checkboxes are visual only; no bulk action is implemented.
- The dashboard portfolio legend/percentages and card sparklines are hard-coded visual elements. The maintenance board’s progress bar is also static.
- Reports have no configurable date range, scheduled delivery, printing, PDF output, usage trends, booking heatmap, or retirement policy.
- The report’s department chart counts assets assigned to departments, not allocation records; “Nearing Review” is merely the ten oldest Available assets.
- The audit Scan Tag button has no implementation. Audit UI becomes read-only after closure, but the audit-item POST view does not independently reject a direct post to a closed cycle.
- Audit creation does not require scope/auditors or validate date order. Closing does not require all items to be assessed.
- Transfer requests may be created by any signed-in user for any asset; they are not restricted to the current holder or to Allocated assets. The data model does not prevent multiple pending transfer requests for the same asset.
- The server-side allocation and transfer forms require at least one holder/destination but do not reject both an employee and a department when manually posted. The dedicated Allocation & Transfer screen adds only browser-side protection.
- Maintenance requests may be raised for Allocated assets. Approval changes asset status to Under Maintenance without closing any existing allocation.
- Booking creation has no future-time restriction and no asset-status check beyond Bookable in the model. A Bookable asset in other non-excluded statuses can therefore be submitted through direct requests.
- User Active/Inactive status is not enforced at login or by permission decorators.
- Only Django staff users can access /admin/. Assigning the custom Admin role in the custom UI does not create staff access, and the custom UI cannot assign Admin at all.
- Asset tag generation uses the current maximum tag plus one, so simultaneous registration can theoretically produce a race condition.

---

## 18. Best Practices

- Create categories and departments before registering assets.
- Keep serial numbers unique and meaningful; they are searchable and enforced as unique.
- Use a consistent location format because audit location scope uses a case-insensitive contains match.
- Set an expected return date for temporary allocations; otherwise the allocation cannot appear in overdue/upcoming-return views.
- Use transfer approval for custody changes to retain allocation history.
- Mark shared resources Bookable only when time-slot reservations are appropriate.
- Check the booking history/timeline before committing a meeting or equipment schedule.
- Use the normal maintenance sequence: approve, assign, start, resolve.
- Assign audit auditors before the audit starts and record notes for Missing/Damaged outcomes.
- Review discrepancy records before closing an audit because Missing outcomes change assets to Lost.
- Treat dashboard decorative charts and broad report labels as navigation aids; use the exact calculations documented in Sections 11 and 13 for operational decisions.
- Use the Django admin site cautiously, because direct data edits may bypass the custom workflow methods and their notifications/activity entries.

---

## 19. Glossary

| Term | Meaning in AssetFlow |
|---|---|
| Asset | A registered organizational resource with a unique asset tag and serial number. |
| Asset tag | Automatically generated identifier in the AF-0001 style. |
| Asset category | Classification of an asset, with optional description and warranty duration in days. |
| Allocation | A record that an asset is currently held by an employee or department, or was returned. |
| Current allocation | The first active allocation associated with an asset. |
| Expected return date | Optional planned return date used for overdue/upcoming dashboard views. |
| Transfer request | A Requested, Approved, or Rejected change of asset destination. |
| Bookable asset | Asset whose Bookable flag is enabled and may be time-slot reserved. |
| Booking | Time interval reservation for a bookable asset. |
| Maintenance request | Issue/service record with Pending, Approved, Rejected, Technician Assigned, In Progress, or Resolved status. |
| Audit cycle | A scoped physical-verification activity with dates, assigned auditors, and audit items. |
| Audit item | One asset’s verification result within a particular audit cycle. |
| Discrepancy | Audit item marked Missing or Damaged. |
| Lost | Asset status applied to Missing audit items when the audit cycle closes. |
| Notification | User-specific in-app message generated by selected workflow events. |
| Activity Log | Shared list of selected operational actions explicitly recorded by views. |

---

## 20. Appendix

### A. High-level routes

AssetFlow has page/form routes, not a REST API. The following is a high-level route inventory.

| Area | Routes |
|---|---|
| Authentication and home | /signup/, /login/, /logout/, / |
| Organization | /org/, /org/departments/new/, /org/departments/<id>/edit/, /org/categories/new/, /org/categories/<id>/edit/, /org/employees/<id>/promote/ |
| Assets | /assets/, /assets/new/, /assets/<id>/, /assets/<id>/edit/, /assets/<id>/allocate/, /assets/<id>/transfer-request/ |
| Transfers and returns | /transfers/, /transfers/<id>/<decision>/, /allocations/<id>/return/ |
| Bookings | /bookings/, /bookings/new/, /bookings/<id>/cancel/ |
| Maintenance | /maintenance/, /maintenance/new/, /maintenance/<id>/<decision>/ (approve or reject), /maintenance/<id>/assign/, /maintenance/<id>/start/, /maintenance/<id>/resolve/ |
| Audits | /audits/, /audits/new/, /audits/<id>/, /audits/<id>/close/, /audit-items/<id>/mark/ |
| Reports | /reports/, /reports/export.csv |
| Notifications and log | /notifications/, /notifications/<id>/read/, /activity-log/ |
| Django administration | /admin/ |

For transfer and maintenance decisions, the final route segment is accepted as a string. The UI supplies approve/reject. The maintenance URL patterns put assign, start, and resolve before the generic decision route so they resolve to their intended views.

### B. Database entities

| Entity | Key data and relationships |
|---|---|
| User | Django AbstractUser extension with role, department, and status. |
| Department | Unique name, optional head, optional self-parent, status; has members/assets/allocations. |
| AssetCategory | Unique name, optional description, optional warranty period days. |
| Asset | Unique asset tag and serial number; category, optional department, lifecycle status, bookable flag, acquisition/location/condition fields. |
| Allocation | Asset with optional employee and/or department holder, timestamps, condition notes, Active/Returned status. |
| TransferRequest | Asset, requested destination employee/department, requester, decision user/time, Requested/Approved/Rejected status. |
| Booking | Asset, booking user, start/end times, cancellation flag, computed display status. |
| MaintenanceRequest | Asset, requester, issue, priority, lifecycle status, technician name, decision/resolution fields. |
| AuditCycle | Name, optional department/location scope, start/end dates, many-to-many auditors, Open/Closed status. |
| AuditItem | Unique audit-cycle/asset pair, result, notes, and checked timestamp. |
| Notification | User, message, read flag, created timestamp. |
| ActivityLog | Optional user, description, created timestamp. |

The applied SQLite schema also contains Django’s standard authentication, session, content-type, permission, migration, and admin-log tables.

### C. Application architecture overview

~~~mermaid
flowchart LR
    Browser["Browser<br/>Tailwind + JavaScript templates"] --> Views["Django Views and Forms"]
    Views --> RBAC["Login and Role Checks"]
    Views --> Models["Workflow Model Methods"]
    Models --> SQLite[("SQLite db.sqlite3")]
    Models --> Notices["Notification and ActivityLog records"]
    Views --> Templates["Server-rendered core templates"]
    Templates --> Browser
    Admin["Django /admin/"] --> SQLite
~~~

### D. Project folder structure

~~~text
AssetFlow-Enterprise-Asset-Resource-Management-System/
├── config/                     Django project settings and root URLs
├── core/
│   ├── management/commands/    seed_demo command
│   ├── migrations/             Initial database migration
│   ├── templates/core/         Page templates and sidebar include
│   ├── templatetags/           Status-pill template filter
│   ├── admin.py                Django admin registration
│   ├── forms.py                Custom forms and field choices
│   ├── models.py               Entities and workflow rules
│   ├── urls.py                 Application URL routes
│   ├── views.py                Page and workflow handlers
│   └── tests.py                Automated workflow tests
├── db.sqlite3                  SQLite development database
├── manage.py                   Django management entry point
├── requirements.txt            Python dependency declaration
├── README.md                   Developer-oriented project notes
├── run.txt                     Run instructions
└── USER_MANUAL.md              This manual
~~~

There is no project static-assets directory and no media-upload directory in the repository.

### E. Configuration overview

| Setting area | Implemented configuration |
|---|---|
| Database | SQLite database at project-root db.sqlite3 |
| Authentication | Custom core.User model; login route named login; dashboard post-login redirect; login post-logout redirect |
| Password validation | Django similarity, minimum-length, common-password, and numeric-password validators |
| Time | UTC time zone; timezone-aware Django dates/times enabled |
| Templates | App template discovery with Django auth/messages/request context and custom unread-notification context |
| Static | STATIC_URL is static/; no collected/static asset configuration is included |
| Security posture | DEBUG enabled, wildcard allowed hosts, and a development secret key in source; these are not production-safe settings |
| Environment variables | None are read by settings.py. The purpose of a conventional .env file would be to externalize settings such as secret key, debug, allowed hosts, database connection, and email service, but such loading is not implemented here. |

### F. Documentation verification

Before this manual was finalized, Django system checks completed with no issues and the repository’s 12 automated tests passed. The tests cover role escalation protection at signup, role promotion, allocation/return/transfer transitions, booking eligibility and overlap checks, maintenance lifecycle, and audit scope/closure behavior.

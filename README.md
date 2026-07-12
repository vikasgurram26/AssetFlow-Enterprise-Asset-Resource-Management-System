# AssetFlow — base code

Django (6.0) + server-rendered templates (Bootstrap 5 via CDN). Same
stack and conventions as the TransitOps build, if anyone on the team saw
that one — same run commands, same file layout philosophy.

## Run it

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo
python manage.py runserver
```

Open `http://127.0.0.1:8000/`. Demo logins (all password `pass1234`
except admin):

| Username | Role |
|---|---|
| `admin` / `admin1234` | Admin — org setup, promotions, `/admin/` back-office |
| `dept_head1` | Department Head — heads IT |
| `asset_mgr1` | Asset Manager — registers/allocates assets, approves things |
| `priya` | Employee — holds the seeded laptop (matches the brief's own worked example) |
| `raj` | Employee — has an overdue allocation, for testing the dashboard's overdue panel |

Try `/signup/` too — it only ever creates an Employee account, by design.

## The rule that mattered most to get right

**Nobody can pick their own role.** Signup (`views.signup`) hardcodes
`user.role = User.Role.EMPLOYEE` after the form saves, regardless of
what's posted — verified this holds even if someone manually injects a
`role` field into the POST body (tested it; the form has no such field,
Django just ignores the extra key). The only path to Department Head /
Asset Manager / Admin is `views.promote_employee`, gated by
`@role_required("ADMIN")`, reachable only from the Employee Directory tab
in Organization Setup. If your team adds any other way to set `role`,
you've reopened the exact hole the brief calls out by name.

## Every mandatory business rule is enforced in `core/models.py`, not scattered across views

Same pattern as before — each rule lives as a method on the model it
governs, with a docstring naming which brief requirement it implements:

- `Allocation.create_for()` — blocks double-allocation, raises the exact
  "currently held by X" message from the brief's example
- `TransferRequest.approve()` — closes the old allocation, opens a new
  one, so history updates automatically
- `Booking.create_for()` — the overlap check is the standard interval
  test (`existing.start < new.end AND existing.end > new.start`);
  verified against the brief's own example numbers (9:00–10:00 existing,
  9:30–10:30 rejected, 10:00–11:00 accepted)
- `MaintenanceRequest.approve()` — flips the asset to Under Maintenance
  at approval, not at request time
- `AuditCycle.close()` — flips Missing items to Lost

## A bug worth knowing about, found via testing not inspection

The maintenance workflow's `/assign/`, `/start/`, `/resolve/` URLs were
originally registered AFTER a wildcard `<str:decision>` pattern that
matches any string — Django resolves URLs in list order, so all three
were silently getting swallowed by the wrong view and routed into a
`reject()` call that then failed validation and did nothing. Found this
by actually running the full workflow through the test client rather
than trusting the code by inspection — worth doing the same for whatever
you build next. Fixed in `core/urls.py`; the comment there explains it so
nobody reintroduces it by adding a new maintenance sub-action above the
wildcard line instead of below it.

## What's simplified versus the full brief — deliberately, not accidentally

- **Reports & Analytics**: category/department breakdowns and a
  most-maintained list are there; utilization *trends* and the booking
  *heatmap* aren't — those need a time-series aggregation this base
  doesn't build yet. The raw data (`Booking`, `Allocation` timestamps) is
  all there for whoever picks this up.
- **Asset category custom fields**: one generic `warranty_period_days`
  field rather than a dynamic per-category schema. Real dynamic fields
  are a bigger feature than an 8-hour base should attempt.
- **Photo/document attachments** on assets and maintenance requests:
  not implemented. Add `ImageField`/`FileField` to `Asset` and
  `MaintenanceRequest` when you're ready — needs `Pillow` and
  `MEDIA_ROOT`/`MEDIA_URL` settings, about 20 minutes of work.
- **Asset Tag generation** (`Asset._generate_asset_tag`) uses max+1,
  which has a narrow race condition if two people register an asset in
  the exact same instant. Fine at hackathon scale; noted in the code
  rather than hidden.

## Where to work without colliding

Same division-of-labor logic as before — pick by module, `core/models.py`
is the one shared file (talk before changing it):

1. **Org setup + Auth** — `signup`, `login_view`, `org_setup`,
   `department_*`, `category_*`, `promote_employee`. This has to be
   solid first; Departments and Categories are foreign keys everywhere
   else.
2. **Assets + Allocation/Transfer** — the biggest, most rule-dense
   module. Good pairing candidate.
3. **Booking + Maintenance** — two independent workflow modules, each
   fully self-contained.
4. **Audit + Reports + Notifications/Activity log** — the "oversight"
   layer; naturally comes together once 1–3 have real data flowing.

Django admin at `/admin/` is your fallback back-office for anything not
built out in the custom UI yet — same as the TransitOps project.

# Physician-to-Physician Consultation Platform — Copilot Build Guide

## 1. Product Goal

Build a web platform where licensed physicians can book paid consultation sessions with other physicians.

The platform should support:

- Public physician discovery
- Physician profile pages
- Physician availability management
- Booking and payment through MyFatoorah
- Admin-managed physician creation and approval
- Consultation scheduling
- Email notifications
- Secure backend workflows
- A strong admin panel for operations

This is an English-only product. Do not add bilingual/RTL support unless explicitly requested later.

---

## 2. Recommended Stack

Use this architecture:

```txt
Frontend:
Next.js + TypeScript + Tailwind CSS + shadcn/ui

Backend:
Django + Django REST Framework

Admin:
Django Admin

Database:
PostgreSQL

Background Jobs:
Celery + Redis

Payments:
MyFatoorah API + webhook confirmation

Email:
Resend or SMTP

Deployment:
Frontend on Vercel
Backend on Railway, Render, Fly.io, or AWS
Database on PostgreSQL
Redis for Celery broker
```

The frontend and backend should be separate applications.

---

## 3. Repository Structure

Create a monorepo:

```txt
physician-consult-platform/
├── frontend/
│   ├── app/
│   ├── components/
│   ├── lib/
│   ├── types/
│   ├── public/
│   ├── package.json
│   └── .env.example
│
├── backend/
│   ├── config/
│   ├── accounts/
│   ├── physicians/
│   ├── bookings/
│   ├── payments/
│   ├── notifications/
│   ├── audit/
│   ├── manage.py
│   ├── requirements.txt
│   └── .env.example
│
├── docker-compose.yml
├── README.md
└── COPILOT_BUILD_GUIDE.md
```

---

## 4. Core User Roles

Implement these roles:

```txt
Admin:
- Can access Django Admin
- Can create and edit physicians
- Can approve or suspend physicians
- Can view bookings and payments
- Can manage specialties

Consulting Physician:
- Has a profile page
- Can offer consultation sessions
- Can set availability
- Can receive bookings

Booking Physician:
- Can browse physicians
- Can book consultations
- Can pay through MyFatoorah
- Can view booking history
```

For the MVP, a user can be both a consulting physician and a booking physician.

---

## 5. Core Backend Apps

Create these Django apps:

```txt
accounts
physicians
bookings
payments
notifications
audit
```

---

## 6. Database Models

### 6.1 Accounts

Use Django's built-in user system or a custom user model.

Prefer a custom user model from the beginning.

Model: `User`

Fields:

```txt
id
email
full_name
phone_number
is_active
is_staff
is_superuser
date_joined
```

Authentication can initially use email + password.

---

### 6.2 Specialties

Model: `Specialty`

Fields:

```txt
id
name
slug
description
is_active
display_order
created_at
updated_at
```

Admin requirements:

- Search by name
- Filter by active status
- Sort by display order
- Slug auto-generates from name

---

### 6.3 Physician Profile

Model: `PhysicianProfile`

Fields:

```txt
id
user
full_name
slug
specialty
subspecialty
professional_title
license_number
license_country
hospital_or_clinic
years_of_experience
bio
consultation_price
consultation_duration_minutes
profile_photo
is_verified
is_featured
accepts_bookings
admin_notes
created_at
updated_at
```

Rules:

- A physician cannot receive bookings unless:
  - `is_verified = true`
  - `accepts_bookings = true`
  - consultation price is set
  - consultation duration is set
- Slug should auto-generate from full name.
- Admin should be able to manually edit slug if needed.

Admin requirements:

- Search by name, email, license number, hospital/clinic
- Filter by specialty, verified status, featured status, accepts bookings
- Inline display of consultation price and duration
- Bulk actions:
  - Mark verified
  - Mark unverified
  - Enable bookings
  - Disable bookings
  - Feature physicians
  - Unfeature physicians

---

### 6.4 Physician Credentials

Model: `PhysicianCredential`

Fields:

```txt
id
physician
credential_type
title
issuing_body
license_number
issued_date
expiry_date
document_file
verification_status
reviewed_by
reviewed_at
admin_notes
created_at
updated_at
```

Credential types:

```txt
medical_license
board_certification
fellowship
degree
other
```

Verification statuses:

```txt
pending
approved
rejected
expired
```

Admin requirements:

- Inline credentials inside PhysicianProfile admin
- Admin can approve/reject credentials
- Show document links using secure/private file handling later

---

### 6.5 Availability

Model: `PhysicianAvailability`

Fields:

```txt
id
physician
weekday
start_time
end_time
is_active
created_at
updated_at
```

Weekday choices:

```txt
0 = Monday
1 = Tuesday
2 = Wednesday
3 = Thursday
4 = Friday
5 = Saturday
6 = Sunday
```

Rules:

- Availability defines recurring weekly availability.
- Booking slots should be generated dynamically from availability and consultation duration.
- Prevent overlapping availability blocks for the same physician.

---

### 6.6 Availability Exceptions

Model: `AvailabilityException`

Fields:

```txt
id
physician
date
start_time
end_time
exception_type
reason
created_at
updated_at
```

Exception types:

```txt
unavailable
extra_available
```

Use this for holidays, blocked time, or special extra availability.

---

### 6.7 Booking

Model: `Booking`

Fields:

```txt
id
booking_reference
requesting_physician
consulting_physician
scheduled_start
scheduled_end
status
case_summary
meeting_url
cancellation_reason
cancelled_by
cancelled_at
created_at
updated_at
```

Booking statuses:

```txt
draft
pending_payment
confirmed
completed
cancelled
no_show
refunded
```

Rules:

- A booking starts as `draft` or `pending_payment`.
- It becomes `confirmed` only after MyFatoorah payment is confirmed by webhook or verified payment lookup.
- Prevent double-booking for the same consulting physician.
- Prevent booking in the past.
- Prevent booking with unverified physicians.
- Prevent booking with physicians who do not accept bookings.
- Generate a unique `booking_reference`.

---

### 6.8 Payment

Model: `Payment`

Fields:

```txt
id
booking
provider
provider_invoice_id
provider_payment_id
amount
currency
status
raw_request
raw_response
paid_at
failed_at
created_at
updated_at
```

Provider:

```txt
myfatoorah
```

Payment statuses:

```txt
initiated
pending
paid
failed
cancelled
refunded
```

Rules:

- Every paid booking should have one payment record.
- Store MyFatoorah invoice/payment IDs.
- Store webhook payloads for debugging and audit.
- Do not mark a booking confirmed based only on frontend redirect.
- Confirm payments using webhook or backend verification call.

---

### 6.9 Audit Log

Model: `AuditLog`

Fields:

```txt
id
actor
action
object_type
object_id
metadata
created_at
```

Use this for admin-sensitive actions:

- Physician approved
- Physician suspended
- Booking cancelled
- Refund marked
- Payment manually checked
- Credential approved/rejected

---

## 7. API Design

Base API path:

```txt
/api/
```

Use Django REST Framework.

---

### 7.1 Public APIs

#### List physicians

```txt
GET /api/physicians/
```

Query params:

```txt
specialty
search
featured
page
```

Return only physicians where:

```txt
is_verified = true
accepts_bookings = true
```

#### Physician detail

```txt
GET /api/physicians/{slug}/
```

Return:

```txt
physician profile
specialty
price
duration
bio
availability preview
```

#### Specialties

```txt
GET /api/specialties/
```

Return active specialties ordered by display order.

---

### 7.2 Availability APIs

#### Get available slots

```txt
GET /api/physicians/{slug}/available-slots/?date=YYYY-MM-DD
```

Rules:

- Generate slots based on recurring availability.
- Apply availability exceptions.
- Remove slots already booked.
- Remove past slots.
- Use consulting physician's consultation duration.

Return:

```json
{
  "date": "2026-06-10",
  "slots": [
    {
      "start": "2026-06-10T10:00:00+03:00",
      "end": "2026-06-10T10:30:00+03:00"
    }
  ]
}
```

---

### 7.3 Booking APIs

#### Create booking

```txt
POST /api/bookings/
```

Input:

```json
{
  "consulting_physician_id": 1,
  "scheduled_start": "2026-06-10T10:00:00+03:00",
  "case_summary": "Need a cardiology opinion on..."
}
```

Behavior:

- Validate physician availability.
- Create booking as `pending_payment`.
- Create MyFatoorah invoice/payment URL.
- Return payment URL.

Output:

```json
{
  "booking_reference": "BK-20260610-0001",
  "payment_url": "https://..."
}
```

#### Booking detail

```txt
GET /api/bookings/{booking_reference}/
```

Must require authentication and authorization.

#### My bookings

```txt
GET /api/me/bookings/
```

Return bookings where current user is either requesting physician or consulting physician.

---

### 7.4 Payment APIs

#### MyFatoorah callback

```txt
GET /api/payments/myfatoorah/callback/
```

Behavior:

- Do not trust this alone.
- Show user a payment-processing or success page after verifying payment status.

#### MyFatoorah error callback

```txt
GET /api/payments/myfatoorah/error/
```

Behavior:

- Show user payment failed/cancelled message.

#### MyFatoorah webhook

```txt
POST /api/payments/myfatoorah/webhook/
```

Behavior:

- Verify webhook authenticity if supported.
- Store raw payload.
- Look up payment/invoice.
- Mark Payment as paid/failed.
- Mark Booking as confirmed only when payment is confirmed.
- Send confirmation emails.

---

## 8. MyFatoorah Payment Flow

Implement payment flow like this:

```txt
1. User selects physician and slot.
2. User submits booking form.
3. Backend validates slot.
4. Backend creates Booking with status pending_payment.
5. Backend creates Payment with status initiated.
6. Backend calls MyFatoorah to create/execute payment.
7. Backend stores invoice/payment identifiers.
8. Backend returns payment_url to frontend.
9. Frontend redirects user to MyFatoorah.
10. MyFatoorah redirects user back to callback URL.
11. Backend verifies payment status.
12. MyFatoorah webhook confirms final payment status.
13. Backend marks Payment as paid.
14. Backend marks Booking as confirmed.
15. Backend sends confirmation email to both physicians.
```

Important:

- Webhook/verification is the source of truth.
- Never confirm booking only because the user reached the success page.
- Handle duplicate webhooks idempotently.
- If the same webhook arrives twice, do not create duplicate side effects.

Environment variables:

```txt
MYFATOORAH_API_KEY=
MYFATOORAH_BASE_URL=
MYFATOORAH_CALLBACK_URL=
MYFATOORAH_ERROR_URL=
MYFATOORAH_WEBHOOK_SECRET=
DEFAULT_CURRENCY=USD
```

---

## 9. Frontend Pages

Use Next.js App Router.

Pages:

```txt
/
```

Landing page with:

- Hero section
- Search by specialty/name
- Featured physicians
- How it works
- CTA to browse physicians

```txt
/physicians
```

Physician listing page:

- Search input
- Specialty filter
- Physician cards
- Price
- Duration
- View profile button

```txt
/physicians/[slug]
```

Physician profile page:

- Photo
- Name
- Specialty
- Professional title
- Bio
- Price
- Duration
- Available date selector
- Available slots
- Book consultation button

```txt
/book/[physicianSlug]
```

Booking page:

- Selected physician
- Selected date/time
- Case summary
- Confirm and pay button

```txt
/payment/success
```

Payment success/processing page.

```txt
/payment/error
```

Payment failed/cancelled page.

```txt
/dashboard
```

Authenticated user dashboard:

- Upcoming consultations
- Past consultations
- Payment status
- Meeting links

```txt
/dashboard/availability
```

Consulting physician availability management.

---

## 10. Frontend Components

Create reusable components:

```txt
PhysicianCard
PhysicianSearchFilters
SpecialtySelect
AvailabilityCalendar
SlotPicker
BookingSummary
PaymentButton
DashboardBookingCard
StatusBadge
PageHeader
LoadingSkeleton
EmptyState
```

Use Tailwind CSS and shadcn/ui.

Design style:

- Professional medical SaaS feel
- Clean white background
- Blue/teal accent
- Clear calls to action
- Mobile responsive
- Avoid clutter

---

## 11. Django Admin Requirements

Customize Django Admin heavily.

Admin sections:

```txt
Users
Physicians
Specialties
Credentials
Availability
Bookings
Payments
Audit Logs
```

### Physician Admin

Show columns:

```txt
full_name
specialty
license_number
consultation_price
consultation_duration_minutes
is_verified
accepts_bookings
is_featured
created_at
```

Filters:

```txt
specialty
is_verified
accepts_bookings
is_featured
license_country
```

Search:

```txt
full_name
user__email
license_number
hospital_or_clinic
```

Inline:

```txt
credentials
availability
availability exceptions
```

Actions:

```txt
mark_verified
mark_unverified
enable_bookings
disable_bookings
mark_featured
unmark_featured
```

### Booking Admin

Show columns:

```txt
booking_reference
requesting_physician
consulting_physician
scheduled_start
status
created_at
```

Filters:

```txt
status
scheduled_start
consulting_physician
```

Search:

```txt
booking_reference
requesting_physician__full_name
consulting_physician__full_name
```

Admin actions:

```txt
mark_completed
mark_no_show
cancel_booking
```

### Payment Admin

Show columns:

```txt
booking
provider
provider_invoice_id
amount
currency
status
paid_at
created_at
```

Filters:

```txt
provider
status
currency
created_at
```

Search:

```txt
provider_invoice_id
provider_payment_id
booking__booking_reference
```

---

## 12. Booking Validation Rules

Implement booking validation in backend services, not only serializers.

Rules:

```txt
- Consulting physician must exist.
- Consulting physician must be verified.
- Consulting physician must accept bookings.
- Scheduled start must be in the future.
- Scheduled end = scheduled start + physician consultation duration.
- Slot must fall inside availability.
- Slot must not overlap existing confirmed or pending_payment bookings.
- Case summary is required.
- User cannot book with themselves unless explicitly allowed later.
```

Use database transactions for booking creation.

Use row locking or uniqueness constraints where appropriate to prevent race conditions.

---

## 13. Time Zone Handling

Use timezone-aware datetimes everywhere.

Default timezone:

```txt
Asia/Kuwait
```

Backend:

```txt
USE_TZ = True
TIME_ZONE = "Asia/Kuwait"
```

Frontend:

- Display times in Kuwait time for MVP.
- Store and send ISO datetimes.
- Avoid manually constructing ambiguous local times.

---

## 14. Email Notifications

Send emails for:

```txt
booking_pending_payment
booking_confirmed_requesting_physician
booking_confirmed_consulting_physician
booking_cancelled
consultation_reminder_24h
consultation_reminder_1h
payment_failed
```

Use a `notifications` app.

Use Celery for reminders.

---

## 15. Celery Jobs

Create scheduled/background tasks:

```txt
send_booking_confirmation_emails
send_24h_consultation_reminders
send_1h_consultation_reminders
expire_unpaid_bookings
mark_past_bookings_ready_for_completion
```

Unpaid booking expiry rule:

```txt
If booking is pending_payment for more than 30 minutes, mark it cancelled or expired.
```

Do not expire if payment is already paid.

---

## 16. Security Requirements

Implement these from the beginning:

```txt
- Use HTTPS in production.
- Store secrets only in environment variables.
- Never expose MyFatoorah API key to frontend.
- Use CSRF protection where appropriate.
- Use CORS only for trusted frontend domain.
- Validate all booking/payment transitions server-side.
- Use authentication for dashboards.
- Use object-level permissions for bookings.
- Users can only view bookings they are part of.
- Admin-only endpoints must require staff permissions.
- Store payment webhook payloads for audit.
```

Do not store sensitive clinical documents in public storage.

If file uploads are added later:

```txt
- Use private storage
- Signed URLs
- File size limits
- File type validation
- Virus scanning if possible
```

---

## 17. MVP Scope

Build MVP in this order.

### Phase 1 — Backend foundation

```txt
- Create Django project
- Add PostgreSQL support
- Add Django REST Framework
- Create custom User model
- Create Specialty model
- Create PhysicianProfile model
- Create Django Admin customizations
- Seed sample specialties and physicians
```

### Phase 2 — Public frontend

```txt
- Create Next.js app
- Build landing page
- Build physician listing page
- Build physician detail page
- Connect to backend APIs
```

### Phase 3 — Availability and booking

```txt
- Create availability models
- Build slot generation service
- Create available slots API
- Create booking model
- Create booking API
- Add booking form in frontend
```

### Phase 4 — MyFatoorah

```txt
- Create payment model
- Add MyFatoorah service wrapper
- Create payment initiation flow
- Add callback endpoint
- Add webhook endpoint
- Confirm bookings after payment
```

### Phase 5 — Dashboard and notifications

```txt
- Add user dashboard
- Show upcoming and past bookings
- Add email notifications
- Add Celery reminders
- Add unpaid booking expiry
```

### Phase 6 — Polish and production readiness

```txt
- Add loading states
- Add error states
- Add empty states
- Improve admin filters/search/actions
- Add audit logs
- Add deployment config
- Add README setup instructions
```

---

## 18. API Response Style

Use consistent API responses.

Success:

```json
{
  "success": true,
  "data": {}
}
```

Error:

```json
{
  "success": false,
  "error": {
    "code": "slot_unavailable",
    "message": "This consultation slot is no longer available."
  }
}
```

Use meaningful error codes:

```txt
physician_not_verified
physician_not_accepting_bookings
slot_unavailable
payment_failed
booking_not_found
permission_denied
```

---

## 19. Coding Style

Backend:

```txt
- Keep business logic in services.py, not views.
- Keep serializers focused on validation and representation.
- Use transactions for booking/payment creation.
- Use clear status transition functions.
- Add model methods where useful.
- Add type hints where practical.
```

Frontend:

```txt
- Use TypeScript.
- Use server components where appropriate.
- Use client components for interactive booking widgets.
- Keep API functions in frontend/lib/api.ts.
- Create typed interfaces in frontend/types/.
- Use loading skeletons for physician cards and slot picker.
```

---

## 20. Suggested Django Services

Create services:

```txt
bookings/services.py
payments/services.py
physicians/services.py
notifications/services.py
```

Important service functions:

```txt
generate_available_slots(physician, date)
validate_booking_slot(physician, scheduled_start)
create_pending_booking(user, physician, scheduled_start, case_summary)
initiate_myfatoorah_payment(booking)
confirm_myfatoorah_payment(payload)
mark_booking_confirmed(booking, payment)
expire_unpaid_bookings()
```

---

## 21. Suggested MyFatoorah Service Interface

Create:

```txt
backend/payments/myfatoorah.py
```

Functions:

```txt
create_payment_url(booking, payment)
get_payment_status(payment_id_or_invoice_id)
handle_webhook(payload, headers)
```

Do not put MyFatoorah logic directly inside views.

---

## 22. Initial Seed Data

Create a management command:

```txt
python manage.py seed_initial_data
```

Seed specialties:

```txt
Cardiology
Dermatology
Endocrinology
Gastroenterology
Neurology
Obstetrics and Gynecology
Oncology
Orthopedics
Pediatrics
Psychiatry
Radiology
Urology
```

Create a few sample physicians for local testing.

---

## 23. Local Development

Use Docker Compose for:

```txt
PostgreSQL
Redis
```

Example services:

```txt
db
redis
backend
frontend
celery
celery-beat
```

The project should support running frontend and backend separately during development.

---

## 24. Environment Variables

### Backend `.env.example`

```txt
DJANGO_SECRET_KEY=
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1

DATABASE_URL=postgres://postgres:postgres@localhost:5432/physician_consult

REDIS_URL=redis://localhost:6379/0

FRONTEND_BASE_URL=http://localhost:3000
BACKEND_BASE_URL=http://localhost:8000

MYFATOORAH_API_KEY=
MYFATOORAH_BASE_URL=
MYFATOORAH_CALLBACK_URL=http://localhost:8000/api/payments/myfatoorah/callback/
MYFATOORAH_ERROR_URL=http://localhost:8000/api/payments/myfatoorah/error/
MYFATOORAH_WEBHOOK_SECRET=
DEFAULT_CURRENCY=USD

EMAIL_HOST=
EMAIL_PORT=
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
DEFAULT_FROM_EMAIL=
```

### Frontend `.env.example`

```txt
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api
NEXT_PUBLIC_SITE_URL=http://localhost:3000
```

---

## 25. Testing Requirements

Backend tests:

```txt
- Physician listing only returns verified/active physicians.
- Cannot book unverified physician.
- Cannot book physician not accepting bookings.
- Cannot book unavailable slot.
- Cannot double-book same physician/time.
- Payment webhook marks payment paid.
- Payment webhook marks booking confirmed.
- Duplicate webhook does not duplicate side effects.
- Pending unpaid booking expires correctly.
```

Frontend tests can be added later, but basic manual flows should be documented.

---

## 26. Definition of Done for MVP

The MVP is done when:

```txt
- Admin can create and verify physicians.
- Admin can add specialties.
- Admin can set physician price and duration.
- Admin can define physician availability.
- Public users can view physicians.
- Public users can select a slot.
- Public users can create a booking.
- User is redirected to MyFatoorah.
- Payment confirmation updates booking status.
- Both physicians receive booking confirmation.
- User can view booking in dashboard.
- Admin can view bookings and payments.
```

---

## 27. Copilot Implementation Instructions

When implementing this project, proceed in small steps.

Do not generate the entire project in one response.

For frontend phases, use the Google Stitch MCP workflow first to create or import the page design, then implement the final production version in Next.js. Treat Stitch output as design scaffolding, not final application architecture.

Use this sequence:

```txt
1. Set up backend Django project.
2. Add core settings, environment variables, PostgreSQL, DRF.
3. Add accounts app with custom user model.
4. Add physicians app and models.
5. Add Django Admin customizations.
6. Add seed data.
7. Add physician public API endpoints.
8. Set up frontend Next.js project.
9. Build landing page and physician listing.
10. Build physician detail page.
11. Add availability and booking backend.
12. Add MyFatoorah payment integration.
13. Add frontend booking flow.
14. Add dashboard.
15. Add notifications and Celery.
16. Add tests and deployment docs.
```

Each step should include:

```txt
- Files to create/change
- Code
- Migration commands
- Test commands
- Manual verification steps
```

Avoid unnecessary features in MVP:

```txt
- No bilingual support
- No mobile app
- No complex chat
- No prescriptions
- No AI summaries
- No ratings/reviews unless requested later
- No multi-country tax logic
- No hospital/team accounts yet
```

---

## 28. Important Product Assumptions

Use these assumptions unless changed later:

```txt
- Product is English only.
- Currency is USD.
- Default timezone is Asia/Kuwait.
- Physicians are manually added or approved by admin.
- MyFatoorah is the payment provider.
- Booking is confirmed only after payment confirmation.
- Admin panel is Django Admin.
- Frontend is a separate Next.js app.
- Backend is Django REST API.
```

## Frontend Design Workflow — Google Stitch + MCP

For the frontend UI, use Google Stitch through an MCP-compatible workflow to help generate and refine page designs before implementing them in Next.js.

Google Stitch should be used as a design and prototyping assistant, not as the final source of truth for production code.

Use Stitch/MCP for:

- Landing page layout
- Physician listing page layout
- Physician profile page layout
- Booking flow screens
- Dashboard screens
- Admin-like frontend dashboards, if needed later
- Visual design direction
- Component layout ideas
- Responsive UI exploration

Production frontend requirements remain:

- Next.js App Router
- TypeScript
- Tailwind CSS
- shadcn/ui components where appropriate
- Clean reusable components
- Accessible HTML
- Responsive layouts
- API integration with Django REST backend

When using Stitch-generated code or layouts:

- Review all generated code before committing.
- Convert generated UI into reusable React components.
- Keep business logic separate from UI components.
- Do not hardcode backend data.
- Replace mock data with typed API calls.
- Ensure forms use proper validation.
- Ensure booking and payment actions call the Django API.
- Ensure the final UI is mobile responsive.
- Ensure accessibility basics are respected: labels, buttons, keyboard focus, semantic HTML.

Stitch-generated output should be treated as a starting point for UI implementation, not as production-ready code.

Recommended workflow:

1. Use Stitch to generate the screen design.
2. Use MCP to bring the design/code into the development environment.
3. Ask Copilot to convert the output into clean Next.js components.
4. Replace mock content with API-driven data.
5. Refactor repeated UI into reusable components.
6. Test responsive behavior.
7. Commit only after manually reviewing the generated code.

Important:

- Do not let Stitch dictate backend structure.
- Do not let Stitch create payment logic.
- Do not expose MyFatoorah keys in frontend code.
- Payment and booking state changes must remain backend-controlled.
# Physician Consult Platform

Physician-to-physician consultation marketplace built with:
- Frontend: Next.js + TypeScript + Tailwind
- Backend: Django + DRF
- Async jobs: Celery + Redis
- Payments: MyFatoorah integration

## Current Build Status

Completed through Phase 6 (polish/production readiness baseline):
- Public physician discovery, profile, booking, payment result pages
- Dashboard and physician availability management (full CRUD)
- Booking/payment/notification/audit backend flows
- Admin action hardening with audit logs
- Docker Compose development stack

## Repository Layout

- `frontend/`: Next.js app
- `backend/`: Django API + admin + Celery tasks
- `docker-compose.yml`: local multi-service stack

## 1) Local Setup (Without Docker)

### Backend

1. Create and activate virtualenv.
2. Install dependencies:

```bash
cd backend
pip install -r requirements.txt
```

3. Create `.env` from `.env.example` and fill required secrets.
4. Run migrations:

```bash
python manage.py migrate
```

5. (Optional) seed sample data:

```bash
python manage.py seed_initial_data
```

6. Start backend:

```bash
python manage.py runserver
```

### Frontend

1. Install dependencies:

```bash
cd frontend
npm install
```

2. Create `.env.local` from the frontend env example values.
3. Start frontend:

```bash
npm run dev
```

Frontend default URL: `http://localhost:3000`
Backend default URL: `http://localhost:8000`

### MyFatoorah Hosted Page in Local Dev

MyFatoorah hosted payment page does not accept `localhost` as redirection URL.
Use a public HTTPS tunnel for your backend callback/error URLs during local development.

1. Start backend on port 8000.
2. Start a tunnel to backend, for example with ngrok:

```bash
ngrok http 8000
```

3. Copy the generated public HTTPS URL (example: `https://abc123.ngrok-free.app`).
4. Update `backend/.env` with tunnel-based URLs:

```txt
BACKEND_BASE_URL=https://abc123.ngrok-free.app
MYFATOORAH_CALLBACK_URL=https://abc123.ngrok-free.app/api/payments/myfatoorah/callback/
MYFATOORAH_ERROR_URL=https://abc123.ngrok-free.app/api/payments/myfatoorah/error/
MYFATOORAH_HOSTED_REDIRECTION_URL=https://abc123.ngrok-free.app/api/payments/myfatoorah/callback/
```

5. Restart backend after changing `.env`.

If your ngrok URL changes, update these values again and restart backend.

### Celery (optional in local non-Docker mode)

Run from `backend/`:

```bash
celery -A config worker --loglevel=info --pool=solo
celery -A config beat --loglevel=info
```

Requires Redis running at `REDIS_URL`.

On Windows, `--pool=solo` is required to avoid `prefork`/`billiard` permission errors.

## 2) Docker Compose Setup

From repository root:

```bash
docker compose up --build
```

Services started:
- `db` (PostgreSQL)
- `redis`
- `backend`
- `celery`
- `celery-beat`
- `frontend`

Stop services:

```bash
docker compose down
```

Reset DB volume:

```bash
docker compose down -v
```

## 3) Environment Variables

### Backend (`backend/.env`)

Base template is available at `backend/.env.example`.

Key values:
- `DJANGO_SECRET_KEY`
- `DJANGO_DEBUG`
- `DJANGO_ALLOWED_HOSTS`
- `DATABASE_URL`
- `REDIS_URL`
- `FRONTEND_BASE_URL`
- `BACKEND_BASE_URL`
- `VIDEO_CONFERENCE_PLACEHOLDER_BASE_URL`
- `USE_CLOUDINARY`
- `CLOUDINARY_CLOUD_NAME`
- `CLOUDINARY_API_KEY`
- `CLOUDINARY_API_SECRET`
- `MYFATOORAH_*`
- `MYFATOORAH_HOSTED_REDIRECTION_URL`
- SMTP/Email settings

For email delivery, two modes are supported:

- `EMAIL_PROVIDER=smtp` (default)
- `EMAIL_PROVIDER=resend` (recommended on Railway if SMTP ports are blocked)

Resend mode variables:

- `RESEND_API_KEY`
- `RESEND_API_URL` (default: `https://api.resend.com/emails`)
- `DEFAULT_FROM_EMAIL` (must be a verified sender/domain in Resend)

If Railway cannot reach SMTP ports (for example errors like `Network is unreachable` on port 587/465), switch to Resend mode.

### Cloudinary Media Storage

Use Cloudinary in production to persist uploaded physician photos across redeploys.

Backend env example values:

```txt
USE_CLOUDINARY=True
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret
```

Notes:
- Keep `USE_CLOUDINARY=False` for local filesystem uploads.
- On Railway, set these values in service environment variables.
- After enabling, restart backend and upload a new physician photo to verify Cloudinary URLs are returned.

### Frontend (`frontend/.env.local`)

Use:

```txt
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api
NEXT_PUBLIC_SITE_URL=http://localhost:3000
```

## 4) Verification Checklist

Backend checks:

```bash
cd backend
python manage.py check
python manage.py test
```

Frontend checks:

```bash
cd frontend
npm run lint
```

## 5) Notes

- Payment confirmation is backend-verified; never trust redirect-only confirmation.
- Availability management routes are authenticated and physician-owned.
- Audit logs capture critical admin and lifecycle actions.

## 6) Vercel Frontend Deploy

This repository is a monorepo, so the frontend lives in `frontend/`.

If Vercel's project settings do not let you pick `frontend/` as the root directory, import the repo normally and let the repo-level `vercel.json` build the app from the subfolder.

Expected setup:

- Framework preset: Next.js
- Install command: `cd frontend && npm ci`
- Build command: `cd frontend && npm run build`

Set the frontend environment variables in Vercel to match `frontend/.env.local`, especially `NEXT_PUBLIC_API_BASE_URL` and `NEXT_PUBLIC_SITE_URL`.

## 7) Railway Backend + Celery Deploy

Deploy backend runtime as three separate Railway services from the same repository:

- `backend` (Django web)
- `celery-worker`
- `beat`

All three should use the same source and image build settings.

### Service Build Configuration (all three)

- Root directory: `backend`
- Builder: Dockerfile
- Dockerfile path: `backend/Dockerfile`

Do not leave the root directory empty for worker/beat. If root directory is `null`, Railway may try a Railpack build from repo root and fail before app startup.

### Service Start Commands

- `backend`: use Dockerfile default command (gunicorn)
- `celery-worker`:

```bash
celery -A config worker --loglevel=info
```

- `beat`:

```bash
celery -A config beat --loglevel=info
```

### Public Networking

- Enable public domain only for `backend`.
- Keep `celery-worker` and `beat` private (no public domain needed).

### Environment Variables Strategy

Use shared variables for common app settings/secrets, and service-scoped variables for runtime connection references.

Recommended shared variables:

- `DJANGO_SECRET_KEY`
- `DJANGO_DEBUG=False`
- `DJANGO_ALLOWED_HOSTS`
- `FRONTEND_BASE_URL`
- `BACKEND_BASE_URL`
- `CORS_ALLOWED_ORIGINS`
- `CSRF_TRUSTED_ORIGINS`
- `USE_CLOUDINARY`
- `CLOUDINARY_*`
- `MYFATOORAH_*`
- `EMAIL_*`
- `DEFAULT_FROM_EMAIL`

Recommended service-scoped variables (set on `backend`, `celery-worker`, `beat`):

- `DATABASE_URL=${{Postgres.DATABASE_URL}}`
- `REDIS_URL=${{Redis.REDIS_URL}}`

Important: do not wrap Railway variable values in quotes.

Correct:

```txt
DJANGO_DEBUG=False
DATABASE_URL=${{Postgres.DATABASE_URL}}
REDIS_URL=${{Redis.REDIS_URL}}
```

Incorrect:

```txt
DJANGO_DEBUG="False"
DATABASE_URL="${{Postgres.DATABASE_URL}}"
REDIS_URL="${{Redis.REDIS_URL}}"
```

Quoted values can break URL parsing and cause startup failures like `dj_database_url.UnknownSchemeError`.

### Deploy Order

1. Deploy `backend`.
2. Confirm web health and run migrations.
3. Deploy `celery-worker`.
4. Deploy `beat`.

### Post-Deploy Checks

- `backend` logs show gunicorn listening and HTTP requests.
- `celery-worker` logs show broker connection and worker ready.
- `beat` logs show scheduler startup and periodic task dispatches.

### Common Failure Fixes

If `beat` fails with Railpack/build-scheduling output only:

1. Set root directory to `backend`.
2. Switch builder to Dockerfile.
3. Ensure dockerfile path is `backend/Dockerfile`.
4. Redeploy `beat`.

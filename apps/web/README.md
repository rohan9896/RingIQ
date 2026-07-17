# RingIQ Web App

Tenant-facing frontend application.

## Stack

- Next.js App Router
- TypeScript
- Clerk with custom auth UI
- Tailwind CSS

## Local Setup

Create a local frontend env file:

```bash
cp apps/web/.env.example apps/web/.env.local
```

Required values:

```text
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=...
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
```

Run the app from the repository root:

```bash
npm run web:dev
```

The dashboard calls the FastAPI `GET /v1/me` endpoint with the active Clerk
session token. The backend currently requires an active Clerk Organization on
the session and matching internal tenant membership rows.

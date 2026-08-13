# LocalFix Setup & Architecture Guide

## Overview

**LocalFix** is a production-grade local service finder and booking platform MVP. It allows customers with urgent service problems (leaks, electrical faults, cleaning) to discover nearby verified service providers, view live availability status, and submit service requests in under 90 seconds.

---

## Repository Structure

```
localfix/
├── backend/
│   ├── app.py                  # Main Flask application & static server entrypoint
│   ├── config.py               # Environment configuration & JWT secrets
│   ├── database.py             # SQLite DB connection & query helper
│   ├── auth.py                 # JWT token management & server-side role check decorators
│   ├── utils/
│   │   ├── geo.py              # Haversine formula geospatial distance calculation
│   │   └── seed.py             # Database seed script with realistic test data
│   ├── routes/
│   │   ├── auth_routes.py      # Registration (/signup), login (/login), profile (/me)
│   │   ├── category_routes.py  # Browse categories & live provider counts
│   │   ├── provider_routes.py  # Search, profile detail, 1-tap availability toggle
│   │   ├── booking_routes.py   # Service request state machine (pending -> accepted -> completed)
│   │   ├── review_routes.py    # Post-completion review submission & rating calculation
│   │   ├── report_routes.py    # Trust & safety report queue
│   │   └── admin_routes.py     # Admin KPIs, verification queue, user moderation
│   └── tests/
│       └── test_app.py         # Automated unit test suite
├── database/
│   ├── schema.sql              # Database table definitions & indexes
│   └── localfix.db             # SQLite database file (created automatically on startup)
├── frontend/
│   ├── index.html              # HTML5 single-page application container
│   ├── css/
│   │   └── styles.css          # Master design system & responsive layout
│   └── js/
│       ├── api.js              # Fetch client wrapper with JWT header interceptors
│       └── app.js              # SPA router, Leaflet map engine, modal handlers, view renderer
└── docs/
    └── SETUP.md                # Local dev documentation
```

---

## Local Setup & Quickstart

### Prerequisites
- Python 3.10+ (Tested on Python 3.14)
- Web browser (Chrome, Firefox, Edge, Safari)

### 1. Install Dependencies & Run Server
No complex node dependencies are required. Run the Flask backend server directly:

```bash
# Navigate to project root
cd localfix

# Run backend app (starts server on http://127.0.0.1:5000)
python backend/app.py
```

*Note: On first startup, if `database/localfix.db` is empty or missing, `app.py` automatically initializes the database schema and populates seed data.*

### 2. Run Automated Unit Tests
To verify auth, role security, Haversine geospatial calculations, and availability toggles:

```bash
python -m unittest discover -s localfix/backend/tests
```

---

## Seed Accounts & Demo Credentials

| Role | Email | Password | Details |
|---|---|---|---|
| **Customer** | `customer@example.com` | `Password123!` | Sample customer account |
| **Provider** | `rajesh.plumber@example.com` | `Password123!` | Rajesh Kumar (Apex Plumbing Solutions) |
| **Provider** | `amit.elec@example.com` | `Password123!` | Amit Sharma (Sharma Electricals) |
| **Provider** | `priya.clean@example.com` | `Password123!` | Priya Verma (Sparkle Clean Home) |
| **Admin** | `admin@example.com` | `AdminPassword123!` | Platform Admin account |

---

## Key Features & User Flows

1. **North Star Customer Flow (<90 seconds)**:
   - Land on homepage → Click "Use My Location" or pick a category (e.g., Plumber).
   - View search results sorted by distance & live availability (🟢 Available / 🟡 Busy / 🔴 Offline).
   - View providers on split List vs. Leaflet Map view.
   - Click "Request Service" → Fill modal → Request lands in provider dashboard inbox.

2. **Provider Dashboard**:
   - 1-Tap Availability control (Available / Busy / Offline) always visible at the top.
   - Accept or Reject incoming pending requests.
   - Advance job state (`accepted` → `in_progress` → `completed`).

3. **Admin Portal**:
   - Protected server-side with `@require_role('admin')` (HTTP 403 returned to unauthorized users).
   - Real-time KPIs: total users, total providers, active available count, total bookings, platform avg rating.
   - Approve or Revoke provider verification badges.
   - User suspension and review moderation.

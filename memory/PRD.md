# Hodler Inn - Product Requirements Document

## Original Problem Statement
Build a two-part application, "Hodler Inn," with a guest portal and an admin backend for managing railroad crew hotel stays.

### Guest Portal Requirements
1. Unified check-in flow for new and returning guests
2. Guests can check in even if not on pre-approved employee list (marked as "pending verification")
3. Guests check out by entering their room number
4. Voice guidance and visual feedback
5. "How to Use" section with video tutorial

### Admin Backend Requirements
1. Dashboard for guest activity reporting
2. Billing and reporting features (Excel, PNG, PDF), with record editing
3. Full CRUD for employee management, including bulk import
4. AI agent to scrape historical data from third-party railroad portal
5. AI daily sync agent to verify stays against railroad portal
6. Telegram notifications for check-ins
7. Bulk verification system for pending guests
8. Employee names auto-update to match railroad portal format during sync
9. AI Phone Agent to handle wake-up calls from CPKC

---

## What's Been Implemented

### Core Guest Portal (Completed)
- [x] Check-in flow with employee verification
- [x] Check-out flow by room number lookup
- [x] Unverified guest check-in with company name validation (CPKC only)
- [x] Voice guidance using Web Speech API (configurable speed from admin)
- [x] Help page with video tutorial
- [x] Sign-in sheet view for guests
- [x] Kiosk mode / fullscreen support
- [x] Auto-idle reset to menu
- [x] Larger signature box (200px) with thicker pen strokes for tablet use
- [x] Security: "Call Help Phone" message after 2 wrong company name attempts

### Admin Dashboard (Completed)
- [x] Employee management (CRUD)
- [x] Bulk employee import
- [x] Booking records management
- [x] Reporting (Excel, PNG, PDF export)
- [x] Guest verification section with bulk approve
- [x] Room management
- [x] Telegram notification settings
- [x] Voice settings: Enable/disable, volume control, **speed control** (0.5-1.2)

### AI Sync Agent (Completed)
- [x] Playwright automation for railroad portal
- [x] Automatic employee ID and room number entry
- [x] Skip already-verified entries (blue checkmark)
- [x] Auto-sync employee names to portal format
- [x] Scheduled daily sync at 3 PM Central

### Latest Updates (March 2026)
- [x] Check-out screen: "On Duty Time" label (removed confusing 24hr format text)
- [x] Voice message: Full instructions for check-in flow
- [x] New employee: Company name field with CPKC validation (case-insensitive)
- [x] Security: Help phone message after 2 failed company name attempts
- [x] Admin: Voice speed control slider (Slow/Normal/Fast)
- [x] Signature box: Bigger + thicker for Fully Kiosk Browser compatibility

---

## Pending/In Progress

### P0 - Critical
- [ ] **AI Daily Sync Confirmation** - Awaiting user feedback on 3 PM auto-sync results

### P1 - High Priority
- [ ] **AI Phone Agent Implementation** - Blocked on Virtual PBX provider info
  - Requirements doc created: `/app/AI_Phone_Agent_Requirements.md`
  - Key tasks: PBX API integration, phone_name field, call routing logic

---

## Future/Backlog

### P2 - Medium Priority
- [ ] Smart Lock Integration (blocked on vendor API research)
- [ ] White-Label SaaS Version (multi-tenant)
- [ ] Blockchain Integration (immutable ledger)

---

## Technical Architecture

```
/app/
├── AI_Phone_Agent_Requirements.md
├── backend/
│   ├── .env
│   ├── requirements.txt
│   ├── server.py          # FastAPI endpoints, voice_speed setting added
│   └── sync_agent.py      # Playwright portal automation
└── frontend/
    └── src/
        ├── index.css
        └── pages/
            ├── AdminDashboard.jsx  # Voice speed slider added
            └── GuestPortal.jsx     # Company name field, bigger signature
```

### Tech Stack
- **Frontend:** React, Tailwind CSS, Shadcn/UI
- **Backend:** FastAPI, pymongo, apscheduler, playwright
- **Database:** MongoDB
- **Integrations:** OpenAI TTS-1, Telegram Bot, Railroad Portal (Playwright)

### Key API Endpoints
- `/api/checkin` - Guest check-in
- `/api/checkout` - Guest check-out
- `/api/guests/register-pending` - Register unverified guest
- `/api/admin/guests/bulk-verify` - Bulk approve pending guests
- `/api/admin/sync/run` - Trigger AI sync agent
- `/api/voice-settings` - Get voice settings (enabled, volume, speed)
- `/api/admin/settings` - Update portal settings including voice_speed

---

## Credentials
- **Admin:** Access at `/admin` with password `hodlerinn2024`

---

## Critical Notes
- **AI Sync Agent:** Uses `keyboard.type()`, clicks at (100, 100) to blur, 5-second wait between fields
- **Company Validation:** Only "CPKC" (case-insensitive) allowed for new employee check-ins
- **Voice Speed:** Configurable from Admin → Portal Settings (0.5 to 1.2)

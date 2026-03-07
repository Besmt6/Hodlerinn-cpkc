# Hodler Inn - Hotel Management System PRD

## Original Problem Statement
Build a comprehensive hotel management system for Hodler Inn that handles:
- Guest check-in/check-out via kiosk
- Employee management and verification
- CPKC railroad crew bookings via email scraping
- API Global Solutions portal sync for billing verification
- Admin dashboard for hotel operations

## User Personas
1. **Hotel Staff** - Check in/out guests, manage rooms
2. **Railroad Crew (CPKC)** - Self-service check-in via kiosk
3. **Hotel Admin** - Manage settings, verify billing, run reports

## Core Requirements
1. Guest Portal (Kiosk) - Self-service check-in/out
2. Admin Dashboard - Full hotel management
3. Email Scraper - Parse CPKC booking PDFs
4. Sync Agent - Verify guests against API Global portal
5. Reporting - PDF exports, billing reports

## Current Architecture
```
/app/
├── backend/
│   ├── server.py        # Main FastAPI app (8100+ lines - NEEDS REFACTORING)
│   ├── sync_agent.py    # Portal sync automation
│   └── requirements.txt
└── frontend/
    └── src/
        ├── pages/
        │   ├── AdminDashboard.jsx
        │   ├── GuestPortal.jsx
        │   └── BookNow.jsx
        └── components/
```

## What's Been Implemented

### March 7, 2026
- ✅ Fixed sync agent hanging on last entry (added timeouts)
- ✅ Fixed "No Bill" auto-click (now only verifies matched entries)
- ✅ Fixed results accumulation bug (reset each sync run)
- ✅ Added late arrival support (queries prev_day, target, next_day)
- ✅ Added PDF report export for sync results
- ✅ Verified Telegram notifications working

### Previous Sessions
- ✅ CPKC Email Scraper (PDF parsing, duplicate handling)
- ✅ Employee Portal Import (530+ employees)
- ✅ Chatbot UI cleanup on /book page
- ✅ Mobile voice fixes (tap-to-start)
- ✅ Auto-removal from Expected Arrivals on check-in
- ✅ Guest verification system
- ✅ Room assignment and billing

## Prioritized Backlog

### P0 - Critical
- [ ] Verify email alerts working (scheduled for tomorrow)

### P1 - High Priority  
- [ ] Refactor server.py into smaller modules (8100+ lines)
- [ ] Production DB sync for cpkc.hodlerinn.com

### P2 - Medium Priority
- [ ] Voice message echo fix on Guest Portal
- [ ] AI Phone Agent (blocked on PBX details)
- [ ] Smart Lock Integration (blocked on vendor API)

### P3 - Future
- [ ] HODL Rewards Token system
- [ ] White-Label SaaS version
- [ ] Code refactoring for AdminDashboard.jsx

## Technical Stack
- **Backend:** FastAPI, Python 3.11
- **Frontend:** React, Tailwind CSS, Shadcn UI
- **Database:** MongoDB Atlas
- **Automation:** Playwright (portal sync)
- **Notifications:** Telegram Bot API
- **PDF:** ReportLab

## Key API Endpoints
- `/api/admin/sync/run` - Run sync agent
- `/api/admin/sync/export-pdf` - Download sync report
- `/api/admin/check-cpkc-emails` - Manual email check
- `/api/admin/collect-employees` - Import from portal
- `/api/book-room` - Guest check-in

## Environment Variables
- `MONGO_URL` - MongoDB connection string
- `TELEGRAM_BOT_TOKEN` - Telegram notifications
- `TELEGRAM_CHAT_ID` - Notification target

## Known Issues
1. server.py is 8100+ lines (needs decomposition)
2. Different MongoDB instances across environments
3. Late arrivals (after midnight) need special handling

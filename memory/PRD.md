# Hodler Inn - Hotel Management System PRD

## Original Problem Statement
Build a comprehensive hotel management system for Hodler Inn, serving railroad crew members (CPKC/BNSF) with automated guest check-in, portal synchronization, AI chatbot concierge (Bitsy), and administrative tools.

## Core Users
1. **Railroad Guests** - Crew members checking in via kiosk
2. **Non-Railroad Guests** - Regular hotel guests
3. **Admin (Kalpesh)** - Hotel owner managing operations

## Implemented Features

### Guest Portal & Check-in
- [x] Guest kiosk interface for railroad crew check-in
- [x] QR code scanning for guest identification
- [x] Room assignment system
- [x] Non-railroad guest check-in flow

### AI Concierge (Bitsy)
- [x] Voice-enabled chatbot on BookNow page
- [x] GPT-5.2 powered conversations
- [x] Text-to-speech responses (OpenAI TTS-1)
- [x] Auto-mic toggle feature
- [x] Rate card display (shows once)

### Sync Agent (Portal Reconciliation)
- [x] Automated sync with API Global Solutions portal
- [x] Playwright-based browser automation
- [x] Date boundary handling (late check-ins after midnight)
- [x] Duplicate entry detection and handling
- [x] PDF report generation for sync results
- [x] 10-minute timeout protection

### Admin Dashboard
- [x] Room management
- [x] Guest records viewing
- [x] Sync job controls with date picker
- [x] PDF report download/view
- [x] Occupancy tracking (NEW - needs testing)

### Email Scraper
- [x] Zoho mail integration for CPKC notifications
- [x] Telegram alerts for new bookings
- [x] Scheduled scraping via APScheduler

### Documents Created
- [x] BlockStay Vision Document (SaaS platform vision)
- [x] Book of Ideas (philosophical insights - 15 chapters)

## Pending Issues (P0-P2)

### P0 - Critical
1. ~~**MongoDB Migration**~~ ✅ COMPLETE - Production using user's Atlas instance
2. **SALTER Duplicate Handling** - Logic deployed, needs verification on March 4th sync

### P1 - Important  
3. **Occupancy Tracking** - UI and endpoints deployed, needs user testing
4. **Email/Telegram Alerts** - User needs to verify if working (duplicate alert fix deployed)
5. **Duplicate Telegram Alerts** - Flag-based fix deployed, awaiting verification

### P2 - Low Priority
6. **Voice Echo on Guest Portal** - Reported but not reproduced

## Recently Completed (March 2026)
- ✅ **CPKC Check-Out Detection** - Green highlighting detection using PyMuPDF
- ✅ **Expected Check-Outs List** - New collection + API + UI for tracking check-outs
- ✅ **MongoDB Migration** - All data in user's Atlas instance
- ✅ **Frontend Routing Fix** - Hash-based routing for page refresh
- ✅ **Automated Zoho Upload** - Sign-in sheets uploaded at 11:59 PM daily
- ✅ **Embeddable Chatbot** - `/bitsy` route for iFrame embedding
- ✅ **Phone Agent Webhook** - `GET /api/webhook/guests` endpoint

## Upcoming Features (Blocked)
- AI Phone Agent - Blocked on SIP/Webhook details from Virtual PBX provider
- Smart Lock Integration - Blocked on vendor API research

## Technical Debt (Critical)
- `server.py` - Monolithic, needs decomposition into routers
- `AdminDashboard.jsx` - Too large, needs component extraction

## Tech Stack
- **Backend:** FastAPI, APScheduler, Playwright, reportlab
- **Frontend:** React, Shadcn/UI, Web Speech API
- **Database:** MongoDB Atlas
- **Integrations:** OpenAI GPT-5.2, OpenAI TTS-1, Telegram, Zoho Mail

## Book of Ideas - Chapters (Dec 2025)
1. The Evolution of Creation
2. Bitcoin as Digital Land
3. The Trust Revolution
4. Privacy as a Right
5. Tokens as Micro-Economies
6. The AI Concierge
7. The Future We're Building
8. Principles for Builders
9. The Sacred Five - Universal Pattern
10. The Dark Truth and Divine Trinity
11. Three Foundations - Physical, Spiritual, Virtual
12. Nature of True Foundations - Flow, Adapt, Accept
13. Bitcoin - The Five Elements of Virtual World
14. Chain of Creation - Five Leads to Five
15. The Borderless Five - Why Human Creations Are Universal

## Key Philosophical Insights Captured
- "Bitcoin is Water for the Virtual World"
- "Bitcoin is Digital Land"
- "5 Elements → Human → 5 Creations → Tech → 5 Foundations → Virtual World"
- "Sanatana Dharma is base of all religions, Bitcoin is base of virtual world"

---
*Last Updated: December 2025*

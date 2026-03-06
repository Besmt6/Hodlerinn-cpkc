# Hodler Inn - Product Requirements Document

## Overview
Full-stack application for managing railroad crew accommodations at Hodler Inn, Heavener, Oklahoma.

**Production URL:** `cpkc.hodlerinn.com`
**Address:** 820 US-59, Heavener, OK 74937
**Phone:** (918) 653-7801

---

## Core Features

### Guest Portal (`/`)
- Touch-friendly kiosk for railroad crew check-in/checkout
- Voice guidance with OpenAI TTS
- Signature capture
- Employee verification against railroad database

### Admin Dashboard (`/admin`)
- Password: `hodlerinn2024`
- Guest records management
- Room management with cleaning status
- Billing reports with Excel/PDF/PNG export
- Employee list management
- Guarantee report for contract tracking
- Portal settings configuration

### Bitsy AI Chatbot (`/book`)
- GPT-5.2 powered booking assistant
- Voice input support (speech-to-text)
- Real-time availability checking
- Respects CPKC expected arrivals (won't oversell)
- Auto-creates reservations in database
- Sends email confirmation + Telegram notification
- Configurable room limits (default 3/day)

### Demo Mode (`/demo`, `/demo/admin`)
- Separate database for demonstrations
- Full interactive check-in/checkout
- Sample data with reset capability
- Safe for showing to prospects

---

## Completed Features (March 2026)

### Session - March 6, 2026
- [x] **Per-Recipient Email Alerts** - Admins can customize which alerts each recipient receives
- [x] **Email Preview** - Preview email content before sending
- [x] **Room # Search** - Quick filter in Guest Records table
- [x] **Bitsy AI Chatbot** - Full conversational booking system
- [x] **Voice Input** - Speech-to-text for chatbot
- [x] **Admin Pricing Settings** - Configurable single/double rates, sales tax
- [x] **Chatbot Room Limit** - Max 3 rooms/day for online bookings
- [x] **Demo Mode** - Separate test environment
- [x] **Manual Backdated Entry** - Add historical check-ins from admin
- [x] **CPKC Email Scraper** - Auto-import expected arrivals from Zoho
- [x] **Expected Arrivals UI** - View/manage in Room Management
- [x] **Revenue Loss Tracking** - For guarantee report when chatbot can't sell

### Previous Sessions
- [x] Non-Railroad Guest & Reservation System
- [x] Daily Status Reports (7 AM & 10 PM)
- [x] Auto-dirty room feature (20 min after checkout)
- [x] Interactive Telegram commands with buttons
- [x] Missing entry tracking from sync
- [x] v11 Auto-sync agent for railroad portal

---

## Key API Endpoints

### Chatbot
- `POST /api/chatbot/message` - Send message to Bitsy
- `POST /api/chatbot/transcribe` - Voice-to-text
- `GET /api/chatbot/availability` - Check room availability

### CPKC Email Integration
- `POST /api/admin/check-cpkc-emails` - Manual email check
- `GET /api/admin/expected-arrivals` - List expected arrivals
- `DELETE /api/admin/expected-arrivals/{id}` - Remove cancelled
- `POST /api/admin/revenue-loss` - Log chatbot denial
- `GET /api/admin/revenue-losses` - For guarantee report

### Email Alerts
- `GET /api/admin/email-alerts/settings` - Get settings
- `POST /api/admin/email-alerts/recipients/add` - Add recipient
- `PUT /api/admin/email-alerts/recipients/alerts` - Update per-recipient alerts
- `GET /api/admin/email-alerts/preview/{type}` - Preview email

### Manual Entry
- `POST /api/admin/manual-entry` - Add backdated check-in

---

## Database Collections

- `bookings` - Guest stay records
- `guests` - Guest profiles
- `employees` - Railroad employee list
- `rooms` - Room inventory
- `blocked_rooms` - Non-railroad guests & reservations
- `expected_arrivals` - CPKC email imports
- `revenue_losses` - Chatbot denial tracking
- `settings` - Portal configuration
- `email_alert_settings` - Alert recipients & preferences

---

## Integrations

- **MongoDB Atlas** - Database
- **OpenAI GPT-5.2** - Chatbot AI (via Emergent LLM Key)
- **OpenAI Whisper** - Voice transcription
- **OpenAI TTS** - Voice guidance
- **Telegram Bot** - Admin notifications
- **Zoho Mail** - Email alerts & CPKC scraping
- **Zoho WorkDrive** - Daily backups
- **API Global Solutions Portal** - Railroad employee sync

---

## Pending Verification
- [ ] Auto-Sync v11 results (EWING, HOLLEY test)
- [ ] Employee Import v2 via portal
- [ ] Voice message echo fix

## Future/Backlog
- [ ] AI Phone Agent (blocked on Virtual PBX info)
- [ ] Smart Lock Integration (blocked on vendor API)
- [ ] Code Refactoring (decompose large files)
- [ ] White-Label SaaS Version

---

## Credentials
- **Admin:** `/admin` with password `hodlerinn2024`
- **CPKC Email Sender:** `aces_support@apiglobalsolutions.com`
- **Frontdesk Email:** `frontdesk@hodlerinn.com`

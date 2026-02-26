# Hodler Inn - Guest Check-In Management System PRD

## Original Problem Statement
Build an app with two use cases: 
1. Guest frontend for Register (employee number, name, signature), Check-In (date/time, room), Check-Out (room, date/time)
2. Hotel admin dashboard showing all details with billing calculation and Excel export

## User Personas
- **Corporate Employees (Guests)**: Use kiosk-style interface for self-service check-in/out
- **Hotel Staff (Admin)**: Access dashboard to view all records and export billing reports

## Core Requirements
- [x] Guest Registration with digital signature
- [x] Guest Check-In with date/time and room selection
- [x] Guest Check-Out with date/time
- [x] Admin login with password protection
- [x] Dashboard with stats and detailed records table
- [x] Billing calculation: >24 hours = 2+ nights
- [x] Excel export for billing reports

## What's Been Implemented (Jan 2026)
- Full-stack app with React frontend + FastAPI backend + MongoDB
- Dark luxury "Vault" theme with gold accents (Hodler Inn branding)
- Digital signature canvas using react-signature-canvas
- Calendar date picker for check-in/out dates
- Admin dashboard with real-time stats
- Excel export using xlsxwriter
- Room occupancy validation
- Employee registration verification

## Technical Stack
- Frontend: React 19, Tailwind CSS, Framer Motion, Shadcn/UI
- Backend: FastAPI, Motor (MongoDB async driver)
- Database: MongoDB
- Dependencies: react-signature-canvas, xlsx, xlsxwriter

## Prioritized Backlog
### P0 (Completed)
- Guest registration, check-in, check-out flows
- Admin dashboard with billing calculation
- Excel export

### P1 (Future)
- Room management (add/edit rooms)
- Date range filtering for reports
- PDF export option

### P2 (Nice to Have)
- Email notifications on check-in/out
- Multi-admin support with roles
- Guest history/loyalty tracking

## Next Tasks
1. Add room management feature
2. Implement date range filters on dashboard
3. Add PDF export option for reports

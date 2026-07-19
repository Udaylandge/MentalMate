# MentalMate - Implementation TODO (Phase 1)

- [x] Create Phase 1 project skeleton:
  - [ ] Create Django project/app structure for all modules (Section 4)
  - [ ] Add base Bootstrap template with nav for Home/Login/Register
  - [ ] Add healthcheck page + route
- [x] Configure MongoDB connectivity using **mongoengine** for the whole project (env vars added; Phase 1 keeps Django DB as sqlite3 for runnable checks)
- [x] Add `.env.example` and wire Django settings to env vars
- [ ] Add minimal run instructions (optional if README not present)
- [x] Verify `python manage.py check` passes (runserver + /healthcheck should work after migrations/release)

# Phase 2 (Authentication) - next steps
- [x] Add EmailVerification model + service layer
- [x] Add register/login/logout/profile views + urls
- [x] Implement email verification flow (login blocked until verified)
- [x] Implement forgot/reset password flow
- [x] Add templates for auth pages
- [x] Add authentication tests per Acceptance Test Checklist (7/7 passing)

# Phase 3 (Mood Logging) - next steps
- [ ] Implement `MoodEntry` model with score validation (1–10) and one-entry-per-day rule
- [ ] Add mood_tracking services layer (create/update/delete/list)
- [ ] Add mood_tracking CRUD views + templates (login protected)
- [ ] Add mood_tracking tests per Acceptance Test Checklist
- [ ] Ensure migrations run and `python manage.py test mood_tracking -v 2` passes

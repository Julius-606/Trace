# 📧 Trace — Public Email Verification Setup

This guide covers the transactional email path that powers **public signup** and **password reset** on the Trace platform (Android app, web portal at `/signup`, and the `/api/auth/*` JSON API).

Since launch, verification codes are **only ever sent to the user's inbox**. They are:

- Generated with Python's `secrets` module (CSPRNG), 6 digits.
- Hashed at rest (PBKDF2-HMAC-SHA256, per-email salt + `OTP_PEPPER_SECRET`). Never stored or logged in plaintext.
- Valid for **10 minutes**, **single-use** (burned on consumption), and locked after **5 failed attempts**.
- Rate-limited: **60-second cooldown** between sends and **3 sends per 5 minutes** per email.
- Absent from API responses — `otp_preview` is `null` unless the development bypass is explicitly enabled.

---

## 1. Configure your SMTP provider

Add these to your `.env` (see `.env.example`, section 8). Any generic SMTP relay works:

| Provider | SMTP_HOST | SMTP_PORT | Notes |
| --- | --- | --- | --- |
| Gmail (App Password) | `smtp.gmail.com` | `587` | Enable 2FA, create an App Password — do **not** use the account password. |
| Brevo | `smtp-relay.brevo.com` | `587` | `SMTP_USER` = your Brevo login, `SMTP_PASSWORD` = SMTP key. |
| SendGrid | `smtp.sendgrid.net` | `587` | `SMTP_USER` = literal `apikey`, `SMTP_PASSWORD` = your API key. |
| Resend | `smtp.resend.com` | `587` | `SMTP_USER` = literal `resend`, `SMTP_PASSWORD` = your API key. Verify your domain first. |
| AWS SES | `email-smtp.<region>.amazonaws.com` | `587` | Verify sender identity + move out of SES sandbox for public sends. |
| Mailpit / MailHog (local dev) | `127.0.0.1` | `1025` | Set `SMTP_USE_TLS=false`. Catch-all inbox, nothing reaches real users. |
| SSL on port 465 | *provider host* | `465` | Set `SMTP_USE_SSL=true` and `SMTP_USE_TLS=false`. |

```bash
SMTP_HOST=smtp.resend.com
SMTP_PORT=587
SMTP_USER=resend
SMTP_PASSWORD=re_xxxxxxxxxxxxxxxx
SMTP_FROM=noreply@your-domain.com   # must be a verified sender on your provider
SMTP_USE_TLS=true
SMTP_USE_SSL=false

OTP_PEPPER_SECRET=<random 64+ char string>   # openssl rand -hex 32
```

> **Deliverability:** set up SPF, DKIM and DMARC for your sending domain or codes **will** land in spam — especially with Gmail/Outlook recipients. Free/forwarding addresses are fine; disposable inbox domains are not blocked yet, so monitor signup abuse after opening enrollment.

## 2. Verify delivery before launch

On the server (with the env vars above set), run:

```bash
cd backend
python scripts/test_smtp.py you@your-domain.com
```

Exit code `0` and a message in the inbox means the public can receive codes. If it prints `[FAIL]`, fix the provider settings it suggests — the backend logs the same delivery errors with the reason.

## 3. Behavior when email is down

`POST /api/auth/send-otp` now **fails loudly** instead of silently dropping codes:

- `SMTP_HOST` unset or delivery throws → **HTTP 503** `"We could not deliver the verification email right now."` An admin alert (`SECURITY`, "Auth OTP delivery FAILED") is recorded. No code is persisted, so the user can simply retry later.
- Android/web clients display the server's `detail` message directly.

This is intentional for public traffic: silent delivery failure permanently strands signups.

## 4. How the flows work

**Signup (Android / `/signup` web / `POST /api/auth/signup`)**
1. Client → `POST /api/auth/send-otp` `{email, action:"signup"}` → user receives the code.
2. Client → `POST /api/auth/signup` with the code. The backend **validates and consumes** the code (PBKDF2 compare, constant-time) and creates the account with `is_email_verified=true`.
3. `POST /api/auth/verify-otp` is a **non-destructive pre-check** (does not burn the code) for clients that want to validate the code before showing the password screen.
4. Re-using a code after signup → `400 No active verification code found`.

**Password reset**
1. `POST /api/auth/send-otp` `{email, action:"forgot_password"}` → 404 if no account (and not only for existing Trace accounts; DebateHub members are also recognized).
2. `POST /api/auth/forgot-password/reset` with the code → password updated, code consumed.

**Browser signup (`POST /signup`)**
Now enforces the same OTP validation before account creation; invalid/expired codes render a "Verification Failed" page and create nothing.

## 5. Development escape hatch (local only!)

```bash
ENABLE_DEV_OTP_BYPASS=true
```

When explicitly enabled:

- The fixed code **`123456`** is accepted for any email/action.
- `otp_preview` is echoed in `/api/auth/send-otp` responses (clients can auto-fill the field).
- Legacy demo passwords (`admin123`, `student123`, …) are accepted on `/api/auth/login`.
- Email delivery may fail without blocking signup (useful offline).

**Defaults OFF. Never set this in production/staging.** Without it, `123456` is rejected and `otp_preview` is always `null`.

## 6. Migrating existing databases

On startup the backend now runs one idempotent cleanup (`UPDATE email_verification_otps SET otp = NULL WHERE otp IS NOT NULL`) that erases plaintext codes written by older versions. No schema change required; the `otp` column remains for compatibility but stays empty. In-flight legacy (10-minute) codes are invalidated by this wipe — affected users just request a fresh code.

## 7. Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| 503 on send-otp | SMTP unreachable/misconfigured | Run `python scripts/test_smtp.py`, check provider dashboard, TLS mode vs port. |
| 429 on send-otp | 60s cooldown / 3-per-5-min cap | Wait; the message tells the user how many seconds. |
| Code rejected after 5 tries | Brute-force lockout | Request a fresh code. |
| Email arrives in spam | Missing SPF/DKIM/DMARC | Authenticate the sending domain at your provider. |
| Gmail "Application-specific password required" | Used account password | Create an App Password (requires 2FA). |
| Works locally, not on HF Spaces | Env vars set in `.env` but HF ignores it | Set the same vars as **Space secrets** in HF settings. |

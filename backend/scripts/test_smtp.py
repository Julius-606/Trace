#!/usr/bin/env python3
"""
Trace SMTP self-check.

Verifies that the transactional email configuration in your environment can
actually deliver a message to a real inbox. Run this on the deployed server
(or locally with the same env vars the backend uses) after setting SMTP_*:

    cd backend
    python scripts/test_smtp.py you@your-domain.com

Exit codes:
    0 - delivery succeeded
    1 - delivery failed (see the error printed; check SMTP_HOST/PORT/ credentials)
    2 - usage error
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Make the failure loud and specific before we even try to connect.
missing = [k for k in ("SMTP_HOST",) if not os.getenv(k)]
if missing:
    print(f"[FATAL] Missing required env var(s): {', '.join(missing)}")
    print("Set SMTP_HOST/SMTP_PORT/SMTP_USER/SMTP_PASSWORD/SMTP_FROM first.")
    sys.exit(2)

from app.core.otp_service import EmailDispatcher, generate_cryptographic_otp  # noqa: E402


def main() -> int:
    if len(sys.argv) != 2 or "@" not in sys.argv[1]:
        print(__doc__)
        return 2

    recipient = sys.argv[1].strip()
    code = generate_cryptographic_otp(length=6)

    print(f"[INFO] SMTP_HOST={os.getenv('SMTP_HOST')} SMTP_PORT={os.getenv('SMTP_PORT', '587')} "
          f"SMTP_USE_TLS={os.getenv('SMTP_USE_TLS', 'true')} SMTP_USE_SSL={os.getenv('SMTP_USE_SSL', 'false')} "
          f"SMTP_FROM={os.getenv('SMTP_FROM') or os.getenv('SMTP_USER') or 'noreply@trace-learning.edu'}")
    print(f"[INFO] Sending test verification email to {recipient} ...")

    delivered = EmailDispatcher.send_otp_email(recipient, code, "signup")
    if delivered:
        print(f"[OK] Test email delivered to {recipient}. Check the inbox (and spam folder).")
        print("[OK] Your users will receive their verification codes. No code value is printed here on purpose.")
        return 0

    print("[FAIL] Delivery failed. Common causes:")
    print("  - SMTP_HOST/SMTP_PORT wrong, or the provider blocks port 25")
    print("  - SMTP_USE_TLS=true against a server without STARTTLS (try SMTP_USE_SSL=true with port 465)")
    print("  - SMTP_USER/SMTP_PASSWORD incorrect (Gmail requires an App Password, not the account password)")
    print("  - Sender address not verified/allowed by the provider (check SMTP_FROM)")
    return 1


if __name__ == "__main__":
    sys.exit(main())

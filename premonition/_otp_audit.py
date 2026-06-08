import sys, json, time, shutil
from pathlib import Path

sys.path.insert(0, 'src')
from premonition.auth.otp_store import OTPStore

# -----------------------------------------------------------
# SECTION A: Audit live otp_records.json for stale/corrupt data
# -----------------------------------------------------------
records_file = Path("logs/auth/otp_records.json")
print("=" * 65)
print("SECTION A: LIVE OTP_RECORDS.JSON AUDIT")
print("=" * 65)
if records_file.exists():
    raw = json.loads(records_file.read_text(encoding="utf-8"))
    for email, rec in raw.items():
        from datetime import datetime, timezone
        expires = datetime.fromisoformat(rec["expires_at"])
        now = datetime.now(timezone.utc)
        expired = now >= expires
        locked = rec.get("locked_until") and now < datetime.fromisoformat(rec["locked_until"])
        print(f"  email            : {email}")
        print(f"  stored key match : {'YES' if email == rec['email'] else 'NO *** KEY MISMATCH ***'}")
        print(f"  expired          : {expired}")
        print(f"  locked           : {bool(locked)}")
        print(f"  attempts         : {rec['attempts']}")
        print(f"  request_count    : {rec['request_count_this_hour']}")
        print()
else:
    print("  No otp_records.json found")

# -----------------------------------------------------------
# SECTION B: End-to-end trace - isolate any email routing bug
# -----------------------------------------------------------
print("=" * 65)
print("SECTION B: E2E EMAIL ROUTING TRACE")
print("=" * 65)

store = OTPStore(Path("_audit_clean"))

test_cases = [
    "user1@gmail.com",
    "user2@gmail.com",
    "user3@outlook.com",
]

summary = []
for entered in test_cases:
    print(f"\n--- Testing: {entered} ---")

    # Step 1: What frontend sends
    frontend_email = entered.strip()
    print(f"  [1] Frontend sends     : '{frontend_email}'")

    # Step 2: Backend request-otp handler
    backend_received = frontend_email  # body.email
    backend_normalized = backend_received.lower()
    print(f"  [2] Backend received   : '{backend_received}'")
    print(f"  [2] Backend normalized : '{backend_normalized}'")

    # Step 3: OTP Store create_otp
    otp, expires_in = store.create_otp(backend_normalized)
    print(f"  [3] OTP generated      : '{otp}' (expires in {expires_in}s)")

    # Step 4: What OTP Store actually saved
    record = store.get_record(backend_normalized)
    print(f"  [4] Stored under key   : '{backend_normalized}'")
    print(f"  [4] record.email       : '{record.email}'")
    print(f"  [4] Keys match         : {backend_normalized == record.email}")

    # Step 5: Resend recipient - from email_service
    resend_to = backend_normalized  # payload["to"] = [to_email]
    print(f"  [5] Resend 'to' field  : '{resend_to}'")

    # Step 6: What frontend sends for verify-otp
    verify_email = frontend_email  # body.email in verify-otp (NOT lowered by frontend)
    verify_normalized = verify_email.lower()
    print(f"  [6] verify-otp email   : '{verify_email}' -> normalized: '{verify_normalized}'")

    # Step 7: Verify the OTP
    success, msg = store.verify_otp(verify_normalized, otp)
    print(f"  [7] Verification       : {'PASS' if success else 'FAIL'} | {msg}")

    # Step 8: Consistency check
    all_match = (
        frontend_email.lower() == backend_normalized ==
        resend_to == record.email == verify_normalized
    )
    print(f"  [8] All emails match   : {'YES' if all_match else 'NO *** ROUTING BUG ***'}")

    summary.append({
        "entered": entered,
        "otp": otp,
        "verify_pass": success,
        "all_match": all_match
    })

shutil.rmtree("_audit_clean", ignore_errors=True)

# -----------------------------------------------------------
# SECTION C: Hardcoded email scan in key files
# -----------------------------------------------------------
print("\n" + "=" * 65)
print("SECTION C: HARDCODED EMAIL SCAN")
print("=" * 65)
scan_files = [
    "src/premonition/auth/otp_store.py",
    "src/premonition/auth/email_service.py",
    "src/premonition/api/routes/auth.py",
    "src/premonition/auth/user_store.py",
    "frontend/src/pages/LoginPage.tsx",
]
hardcoded_patterns = ["doctor@", "admin@", "test@", "gmail.com", "hardcoded", "1234"]
for fpath in scan_files:
    p = Path(fpath)
    if not p.exists():
        print(f"  {fpath}: NOT FOUND")
        continue
    lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
    hits = []
    for i, line in enumerate(lines, 1):
        for pat in hardcoded_patterns:
            if pat.lower() in line.lower() and not line.strip().startswith("#"):
                hits.append((i, line.strip()[:80]))
    if hits:
        print(f"\n  FILE: {fpath}")
        for lineno, text in hits:
            print(f"    L{lineno}: {text}")
    else:
        print(f"  {fpath}: CLEAN")

# -----------------------------------------------------------
# SECTION D: Summary table
# -----------------------------------------------------------
print("\n" + "=" * 65)
print("SECTION D: FINAL PASS/FAIL TABLE")
print("=" * 65)
print(f"  {'Entered Email':<28} {'OTP':>6} {'Verify':>8} {'Routing OK':>12}")
for r in summary:
    print(f"  {r['entered']:<28} {r['otp']:>6} {'PASS' if r['verify_pass'] else 'FAIL':>8} {'YES' if r['all_match'] else 'NO *** BUG':>12}")


import sqlite3
from audit import DB_FILE, log_event, verify_chain

# Ensure there is at least one record.
log_event(
    "invoice_agent",
    "read_invoice",
    "ALLOW",
    0,
    "Tamper detection test"
)

assert verify_chain() is True
print("Before modification: Chain valid")

conn = sqlite3.connect(DB_FILE)

try:
    original = conn.execute("""
        SELECT id, reason
        FROM audit_logs
        ORDER BY id
        LIMIT 1
    """).fetchone()

    record_id, original_reason = original

    conn.execute("""
        UPDATE audit_logs
        SET reason = ?
        WHERE id = ?
    """, ("Modified audit record", record_id))

    conn.commit()

    print("After modification: Chain valid =", verify_chain())

finally:
    # Restore the test database so later demos still work.
    conn.execute("""
        UPDATE audit_logs
        SET reason = ?
        WHERE id = ?
    """, (original_reason, record_id))

    conn.commit()
    conn.close()

assert verify_chain() is True
print("After restoration: Chain valid =", verify_chain())

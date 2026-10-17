
import sqlite3
import json
import hashlib
from pathlib import Path
from datetime import datetime, timezone

DB_FILE = Path(__file__).with_name("agentguard.db")


def connect():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def calculate_hash(record):
    encoded = json.dumps(
        record,
        sort_keys=True,
        separators=(",", ":")
    ).encode("utf-8")

    return hashlib.sha256(encoded).hexdigest()


def init_db():
    with connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                agent TEXT NOT NULL,
                action TEXT NOT NULL,
                decision TEXT NOT NULL,
                risk_score INTEGER NOT NULL,
                reason TEXT NOT NULL,
                previous_hash TEXT NOT NULL,
                record_hash TEXT NOT NULL
            )
        """)


def log_event(agent, action, decision, risk_score, reason):
    timestamp = datetime.now(timezone.utc).isoformat()

    with connect() as conn:
        previous = conn.execute("""
            SELECT record_hash
            FROM audit_logs
            ORDER BY id DESC
            LIMIT 1
        """).fetchone()

        previous_hash = (
            previous["record_hash"] if previous else "GENESIS"
        )

        record = {
            "timestamp": timestamp,
            "agent": agent,
            "action": action,
            "decision": decision,
            "risk_score": risk_score,
            "reason": reason,
            "previous_hash": previous_hash
        }

        record_hash = calculate_hash(record)

        conn.execute("""
            INSERT INTO audit_logs (
                timestamp, agent, action, decision,
                risk_score, reason, previous_hash, record_hash
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            timestamp,
            agent,
            action,
            decision,
            risk_score,
            reason,
            previous_hash,
            record_hash
        ))

    return record_hash


def get_logs():
    with connect() as conn:
        rows = conn.execute("""
            SELECT * FROM audit_logs ORDER BY id DESC
        """).fetchall()

        return [dict(row) for row in rows]


def verify_chain():
    logs = get_logs()
    previous_hash = "GENESIS"

    # Verify from the oldest record to the newest.
    for row in reversed(logs):
        record = {
            "timestamp": row["timestamp"],
            "agent": row["agent"],
            "action": row["action"],
            "decision": row["decision"],
            "risk_score": row["risk_score"],
            "reason": row["reason"],
            "previous_hash": previous_hash
        }

        if row["previous_hash"] != previous_hash:
            return False

        if calculate_hash(record) != row["record_hash"]:
            return False

        previous_hash = row["record_hash"]

    return True


init_db()

import sqlite3
import os
from datetime import datetime

DB_PATH = "data/bastion.db"
LOG_FILE = "logs/bastion.log"


def init_db():
    os.makedirs("data", exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            session_id TEXT,
            risk_score REAL,
            violation_type TEXT,
            decision TEXT,
            integrity_score REAL,
            instruction_depth INTEGER,
            violations INTEGER
        )
    """)

    conn.commit()
    conn.close()


def insert_log(
    session_id,
    risk_score,
    violation_type,
    decision,
    integrity_score,
    instruction_depth,
    violations,
    module_name="RiskEngine"
):
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO audit_logs (
            timestamp,
            session_id,
            risk_score,
            violation_type,
            decision,
            integrity_score,
            instruction_depth,
            violations
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        timestamp,
        session_id,
        risk_score,
        violation_type,
        decision,
        integrity_score,
        instruction_depth,
        violations
    ))

    conn.commit()
    conn.close()

    # Structured file log
    os.makedirs("logs", exist_ok=True)
    with open(LOG_FILE, "a") as f:
        f.write(
            f"{timestamp} | session={session_id} | {module_name} | "
            f"risk_score={risk_score} | violation={violation_type} | "
            f"decision={decision} | integrity_score={integrity_score} | "
            f"instruction_depth={instruction_depth} | violations={violations}\n"
        )


def get_logs(session_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT timestamp, risk_score, decision, integrity_score
        FROM audit_logs
        WHERE session_id = ?
        ORDER BY id DESC
    """, (session_id,))

    rows = cursor.fetchall()
    conn.close()

    result = []
    for row in rows:
        result.append({
            "timestamp": row[0],
            "risk_score": row[1],
            "decision": row[2],
            "integrity_score": row[3]
        })

    return result

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional

from config import DB_PATH


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS sites (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            api_key TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS daily_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            site_id TEXT NOT NULL,
            report_date TEXT NOT NULL,
            csv_data BLOB,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (site_id) REFERENCES sites(id)
        );

        CREATE TABLE IF NOT EXISTS alarms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            site_id TEXT NOT NULL,
            alarm_type TEXT NOT NULL,
            alarm_id TEXT NOT NULL,
            message TEXT NOT NULL,
            severity TEXT NOT NULL,
            value REAL,
            timestamp TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (site_id) REFERENCES sites(id)
        );

        CREATE TABLE IF NOT EXISTS realtime_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            site_id TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'disconnected',
            bits_json TEXT,
            words_json TEXT,
            accum_heat REAL DEFAULT 0,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );
    """)
    conn.commit()
    conn.close()


def register_site(site_id: str, name: str = "", api_key: str = "") -> bool:
    conn = get_conn()
    try:
        conn.execute("INSERT OR IGNORE INTO sites (id, name, api_key) VALUES (?, ?, ?)", (site_id, name or site_id, api_key))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def save_daily_report(site_id: str, report_date: str, csv_data: bytes) -> int:
    conn = get_conn()
    conn.execute("INSERT INTO daily_reports (site_id, report_date, csv_data) VALUES (?, ?, ?)", (site_id, report_date, csv_data))
    conn.commit()
    last_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.close()
    return last_id


def save_alarm(site_id: str, alarm_type: str, alarm_id: str, message: str, severity: str, value: float, timestamp: str) -> int:
    conn = get_conn()
    conn.execute(
        "INSERT INTO alarms (site_id, alarm_type, alarm_id, message, severity, value, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (site_id, alarm_type, alarm_id, message, severity, value, timestamp),
    )
    conn.commit()
    last_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.close()
    return last_id


def save_realtime(site_id: str, timestamp: str, status: str, bits_json: str, words_json: str, accum_heat: float):
    conn = get_conn()
    conn.execute(
        "INSERT INTO realtime_log (site_id, timestamp, status, bits_json, words_json, accum_heat) VALUES (?, ?, ?, ?, ?, ?)",
        (site_id, timestamp, status, bits_json, words_json, accum_heat),
    )
    conn.commit()
    conn.close()


def get_sites() -> list:
    conn = get_conn()
    rows = conn.execute("SELECT * FROM sites ORDER BY name").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_site(site_id: str) -> Optional[dict]:
    conn = get_conn()
    row = conn.execute("SELECT * FROM sites WHERE id = ?", (site_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def update_site(site_id: str, name: str = "", api_key: str = "") -> bool:
    conn = get_conn()
    cursor = conn.execute("UPDATE sites SET name = COALESCE(NULLIF(?, ''), name), api_key = COALESCE(NULLIF(?, ''), api_key) WHERE id = ?", (name, api_key, site_id))
    conn.commit()
    affected = cursor.rowcount
    conn.close()
    return affected > 0


def delete_site(site_id: str) -> bool:
    conn = get_conn()
    cursor = conn.execute("DELETE FROM sites WHERE id = ?", (site_id,))
    conn.commit()
    affected = cursor.rowcount
    conn.close()
    return affected > 0


def get_recent_realtime(site_id: str, limit: int = 100) -> list:
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM realtime_log WHERE site_id = ? ORDER BY id DESC LIMIT ?", (site_id, limit)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_alarms(site_id: Optional[str] = None, limit: int = 50) -> list:
    conn = get_conn()
    if site_id:
        rows = conn.execute(
            "SELECT * FROM alarms WHERE site_id = ? ORDER BY id DESC LIMIT ?", (site_id, limit)
        ).fetchall()
    else:
        rows = conn.execute("SELECT * FROM alarms ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_daily_reports(site_id: Optional[str] = None, limit: int = 10) -> list:
    conn = get_conn()
    if site_id:
        rows = conn.execute(
            "SELECT id, site_id, report_date, created_at FROM daily_reports WHERE site_id = ? ORDER BY id DESC LIMIT ?",
            (site_id, limit),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT id, site_id, report_date, created_at FROM daily_reports ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

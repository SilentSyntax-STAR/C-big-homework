"""SQLite setup. Bookings use unique constraints and transactions for correctness."""
from pathlib import Path
import sqlite3

SCHEMA = '''
CREATE TABLE IF NOT EXISTS students (
    student_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    class_name TEXT NOT NULL,
    instrument TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    registered_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS reservations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id TEXT NOT NULL REFERENCES students(student_id),
    room_no INTEGER NOT NULL CHECK (room_no BETWEEN 1 AND 20),
    reservation_date TEXT NOT NULL,
    slot_hour INTEGER NOT NULL CHECK (slot_hour BETWEEN 7 AND 21),
    status TEXT NOT NULL DEFAULT 'booked'
        CHECK (status IN ('booked','signed_in','signed_out')),
    created_at TEXT NOT NULL,
    checked_in_at TEXT,
    checked_out_at TEXT,
    UNIQUE(reservation_date,slot_hour,room_no),
    UNIQUE(reservation_date,slot_hour,student_id)
);
CREATE INDEX IF NOT EXISTS idx_reservation_student ON reservations(student_id,reservation_date);
CREATE INDEX IF NOT EXISTS idx_reservation_day ON reservations(reservation_date,slot_hour);
'''


def open_database(path):
    if str(path) != ':memory:':
        Path(path).expanduser().parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path), timeout=5, isolation_level=None)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys=ON')
    conn.execute('PRAGMA busy_timeout=5000')
    if str(path) != ':memory:':
        conn.execute('PRAGMA journal_mode=WAL')
    conn.executescript(SCHEMA)
    return conn


def default_database_path():
    return Path.home() / '.hit_piano_rooms_v2' / 'piano_rooms.sqlite3'

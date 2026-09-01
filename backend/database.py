import sqlite3
import os
from typing import Dict, Any, List, Optional

DB_PATH = os.path.join(os.path.dirname(__file__), "krishi_database.db")

def init_db():
    """Initialize SQLite database and create grading_sessions table with status column."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS grading_sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        batch_id TEXT UNIQUE NOT NULL,
        center_id TEXT NOT NULL,
        timestamp TEXT NOT NULL,
        filename TEXT NOT NULL,
        overall_grade TEXT NOT NULL,
        confidence_score REAL NOT NULL,
        grade_a_percentage REAL NOT NULL,
        grade_urs_percentage REAL NOT NULL,
        rejected_percentage REAL NOT NULL,
        damaged_count INTEGER NOT NULL,
        rotten_count INTEGER NOT NULL,
        sprouted_count INTEGER NOT NULL,
        undersized_count INTEGER NOT NULL,
        grade_a_weight_kg REAL NOT NULL,
        grade_urs_weight_kg REAL NOT NULL,
        rejected_weight_kg REAL NOT NULL,
        total_weight_kg REAL NOT NULL,
        moisture_level TEXT NOT NULL,
        firmness_rating TEXT NOT NULL,
        shelf_life_days INTEGER NOT NULL,
        farmer_recommendation TEXT NOT NULL,
        status TEXT DEFAULT 'ACCEPTED'
    )
    """)
    
    # Add status column if table was created previously without status column
    try:
        cursor.execute("ALTER TABLE grading_sessions ADD COLUMN status TEXT DEFAULT 'ACCEPTED'")
    except sqlite3.OperationalError:
        pass  # Column already exists

    conn.commit()
    conn.close()

def log_grading_session(data: Dict[str, Any]) -> str:
    """Inserts a new grading session record into SQLite database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    status = data.get("status", "ACCEPTED")

    cursor.execute("""
    INSERT INTO grading_sessions (
        batch_id, center_id, timestamp, filename, overall_grade, confidence_score,
        grade_a_percentage, grade_urs_percentage, rejected_percentage,
        damaged_count, rotten_count, sprouted_count, undersized_count,
        grade_a_weight_kg, grade_urs_weight_kg, rejected_weight_kg, total_weight_kg,
        moisture_level, firmness_rating, shelf_life_days, farmer_recommendation, status
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data["batch_id"],
        data["center_id"],
        data["timestamp"],
        data["filename"],
        data["overall_grade"],
        data["confidence_score"],
        data["grade_a_percentage"],
        data["grade_urs_percentage"],
        data["rejected_percentage"],
        data["damaged_count"],
        data["rotten_count"],
        data["sprouted_count"],
        data["undersized_count"],
        data["grade_a_weight_kg"],
        data["grade_urs_weight_kg"],
        data["rejected_weight_kg"],
        data["total_weight_kg"],
        data["moisture_level"],
        data["firmness_rating"],
        data["shelf_life_days"],
        data["farmer_recommendation"],
        status
    ))
    
    conn.commit()
    conn.close()
    return data["batch_id"]

def update_session_status(batch_id: str, status: str = "DISPUTED") -> bool:
    """Updates the status column of a specific grading session record in SQLite database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE grading_sessions SET status = ? WHERE batch_id = ?", (status, batch_id))
    rows = cursor.rowcount
    conn.commit()
    conn.close()
    return rows > 0

def get_all_grading_sessions() -> List[Dict[str, Any]]:
    """Retrieves all logged grading sessions ordered by latest timestamp."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM grading_sessions ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_session_by_batch_id(batch_id: str) -> Optional[Dict[str, Any]]:
    """Retrieves a specific grading session by batch ID."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM grading_sessions WHERE batch_id = ?", (batch_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

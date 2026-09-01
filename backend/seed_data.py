import sqlite3
import random
from datetime import datetime, timedelta
import os
from backend.database import DB_PATH, init_db

CENTERS = [
    "APMC-LASALGAON-MAIN-01",
    "APMC-NASHIK-CENTER-04",
    "APMC-PUNE-MARKET-02",
    "APMC-SOLAPUR-CENTER-03",
    "NAFED-AHMEDNAGAR-HUB-05",
    "APMC-DHULE-CENTER-01",
    "APMC-MANMAD-HUB-02"
]

SAMPLE_FILENAMES = [
    "lot_lasalgaon_batch1.jpg",
    "lot_nashik_export_04.jpg",
    "lot_pune_urs_spec.jpg",
    "lot_solapur_harvest.jpg",
    "lot_nafed_procure_89.jpg",
    "lot_dhule_crop_12.jpg"
]

def seed_database():
    """Populates SQLite database with 15 realistic seed rows of past onion grading sessions."""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Clear existing rows to prevent duplicate seed entries
    cursor.execute("DELETE FROM grading_sessions")

    now = datetime.now()

    for i in range(15):
        batch_num = 890 - i * 7
        batch_id = f"BATCH-MH-2026-{batch_num:03d}"
        center_id = random.choice(CENTERS)
        filename = random.choice(SAMPLE_FILENAMES)
        timestamp_dt = now - timedelta(hours=i * 5 + random.randint(1, 4))
        timestamp_str = timestamp_dt.strftime("%Y-%m-%d %H:%M:%S")

        # Varying Grade-A / Grade-URS distributions
        if i % 3 == 0:
            # Premium Grade A batch
            grade_a_pct = round(random.uniform(75.0, 88.0), 1)
            grade_urs_pct = round(random.uniform(10.0, 18.0), 1)
            rejected_pct = round(100.0 - (grade_a_pct + grade_urs_pct), 1)
            overall_grade = "Grade-A"
            damaged_count = random.randint(0, 2)
            rotten_count = 0
            sprouted_count = 0
            undersized_count = random.randint(1, 4)
            shelf_days = 60
            firmness = "Solid & Crisp Shell"
            moisture = "82% (Ideal)"
            rec = "High-value export quality. Meets NAFED/APMC Grade-A criteria for long cold storage."
        elif i % 3 == 1:
            # Moderate Grade URS batch
            grade_a_pct = round(random.uniform(38.0, 52.0), 1)
            grade_urs_pct = round(random.uniform(40.0, 50.0), 1)
            rejected_pct = round(100.0 - (grade_a_pct + grade_urs_pct), 1)
            overall_grade = "Grade-URS"
            damaged_count = random.randint(3, 6)
            rotten_count = random.randint(0, 1)
            sprouted_count = random.randint(0, 2)
            undersized_count = random.randint(4, 9)
            shelf_days = 25
            firmness = "Medium Firm"
            moisture = "88% (Slightly High)"
            rec = "Meets SIH 2026 Under Relaxed Specifications (URS) norms. Sell in local market within 20 days."
        else:
            # Defective / High URS & Rejection batch
            grade_a_pct = round(random.uniform(18.0, 32.0), 1)
            grade_urs_pct = round(random.uniform(42.0, 58.0), 1)
            rejected_pct = round(100.0 - (grade_a_pct + grade_urs_pct), 1)
            overall_grade = "Grade-C" if rejected_pct > 20.0 else "Grade-URS"
            damaged_count = random.randint(4, 8)
            rotten_count = random.randint(2, 5)
            sprouted_count = random.randint(3, 6)
            undersized_count = random.randint(6, 12)
            shelf_days = 8
            firmness = "Soft & Damp"
            moisture = "93% (High Rot Risk)"
            rec = "Defect threshold exceeded (sprouting/rot). Separate affected onions immediately to prevent decay."

        total_sample_kg = 100.0
        grade_a_kg = round(total_sample_kg * (grade_a_pct / 100.0), 2)
        grade_urs_kg = round(total_sample_kg * (grade_urs_pct / 100.0), 2)
        rejected_kg = round(total_sample_kg - (grade_a_kg + grade_urs_kg), 2)
        conf_score = round(random.uniform(93.0, 98.5), 1)

        cursor.execute("""
        INSERT INTO grading_sessions (
            batch_id, center_id, timestamp, filename, overall_grade, confidence_score,
            grade_a_percentage, grade_urs_percentage, rejected_percentage,
            damaged_count, rotten_count, sprouted_count, undersized_count,
            grade_a_weight_kg, grade_urs_weight_kg, rejected_weight_kg, total_weight_kg,
            moisture_level, firmness_rating, shelf_life_days, farmer_recommendation
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            batch_id, center_id, timestamp_str, filename, overall_grade, conf_score,
            grade_a_pct, grade_urs_pct, rejected_pct,
            damaged_count, rotten_count, sprouted_count, undersized_count,
            grade_a_kg, grade_urs_kg, rejected_kg, total_sample_kg,
            moisture, firmness, shelf_days, rec
        ))

    conn.commit()
    conn.close()
    print("Successfully seeded SQLite database with 15 past onion grading session rows!")

if __name__ == "__main__":
    seed_database()

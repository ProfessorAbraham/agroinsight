
# populate_db.py
import datetime
from db import get_connection, create_tables

def populate():
    conn = get_connection()
    create_tables(conn)
    c = conn.cursor()

    # Insert kebeles
    kebeles = [
        ('Adama', 8.55, 39.27),
        ('Bishoftu', 8.75, 39.00),
    ]
    c.executemany('INSERT OR IGNORE INTO kebeles (name, latitude, longitude) VALUES (?, ?, ?)', kebeles)

    # Insert farmers
    farmers = [
        ('Abebe', '+251900000001', 'Adama'),
        ('Bekele', '+251900000002', 'Adama'),
        ('Chala', '+251900000003', 'Bishoftu'),
    ]
    c.executemany('INSERT INTO farmers (name, phone, kebele) VALUES (?, ?, ?)', farmers)

    # Insert pest reports
    now = datetime.datetime.now().isoformat()
    pest_reports = [
        (now, 'Adama', 'maize', 'leaf holes', 'few'),
        (now, 'Adama', 'teff', 'yellow leaves', 'many'),
        (now, 'Bishoftu', 'wheat', 'wilting', 'few'),
    ]
    c.executemany('INSERT INTO pest_reports (report_time, kebele, crop, symptom, severity) VALUES (?, ?, ?, ?, ?)', pest_reports)

    conn.commit()
    conn.close()
    print("Database populated with sample data.")

if __name__ == "__main__":
    populate()

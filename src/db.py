# db.py
import sqlite3
import os

def get_connection(db_path='data/warkadguard.db'):
    db_dir = os.path.dirname(db_path)
    if not os.path.exists(db_dir):
        os.makedirs(db_dir)
    conn = sqlite3.connect(db_path)
    return conn

def create_tables(conn):
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS farmers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT NOT NULL,
            kebele TEXT NOT NULL
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS kebeles (
            name TEXT PRIMARY KEY,
            latitude REAL,
            longitude REAL
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS pest_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            report_time TEXT,
            kebele TEXT,
            crop TEXT,
            symptom TEXT,
            severity TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS satellite_ndvi (
            kebele TEXT,
            date TEXT,
            ndvi_value REAL,
            PRIMARY KEY (kebele, date)
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS weather_data (
            kebele TEXT,
            datetime TEXT,
            temperature REAL,
            humidity REAL,
            rainfall REAL,
            PRIMARY KEY (kebele, datetime)
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS risk_scores (
            kebele TEXT PRIMARY KEY,
            risk_score REAL,
            last_updated TEXT
        )
    ''')
    conn.commit()

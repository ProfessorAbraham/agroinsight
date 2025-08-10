# db.py
import sqlite3
import os

def get_connection(db_path='data/warkadguard.db'):
    db_dir = os.path.dirname(db_path)
    if not os.path.exists(db_dir):
        os.makedirs(db_dir)
    conn = sqlite3.connect(db_path)
    return conn

def get_last_run_date(conn):
    c = conn.cursor()
    c.execute("SELECT value FROM metadata WHERE key='last_run_date'")
    row = c.fetchone()
    return row[0] if row else None

def set_last_run_date(conn, date_str):
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO metadata (key, value) VALUES (?, ?)", ('last_run_date', date_str))
    conn.commit()

def create_metadata_table(conn):
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS metadata (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    ''')
    conn.commit()

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
    # db.py (add below existing functions)

def insert_ndvi(conn, kebele, date, ndvi_value):
    c = conn.cursor()
    c.execute('''
        INSERT OR REPLACE INTO satellite_ndvi (kebele, date, ndvi_value)
        VALUES (?, ?, ?)
    ''', (kebele, date, ndvi_value))
    conn.commit()

def insert_weather(conn, kebele, datetime_str, temperature, humidity, rainfall):
    c = conn.cursor()
    c.execute('''
        INSERT OR REPLACE INTO weather_data (kebele, datetime, temperature, humidity, rainfall)
        VALUES (?, ?, ?, ?, ?)
    ''', (kebele, datetime_str, temperature, humidity, rainfall))
    conn.commit()

def update_risk_score(conn, kebele, risk_score, last_updated):
    c = conn.cursor()
    c.execute('''
        INSERT OR REPLACE INTO risk_scores (kebele, risk_score, last_updated)
        VALUES (?, ?, ?)
    ''', (kebele, risk_score, last_updated))
    conn.commit()

def get_last_run_date(conn):
    c = conn.cursor()
    c.execute("SELECT value FROM metadata WHERE key='last_run_date'")
    row = c.fetchone()
    return row[0] if row else None

def set_last_run_date(conn, date_str):
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO metadata (key, value) VALUES (?, ?)", ('last_run_date', date_str))
    conn.commit()

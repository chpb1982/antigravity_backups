import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), 'trading.db')

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS signals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            sentiment REAL,
            sentiment_status TEXT,
            momentum REAL,
            momentum_status TEXT,
            volume_ratio REAL,
            price_change_pct REAL,
            score INTEGER
        )
    """)
    conn.commit()
    conn.close()

def save_signal(signal: dict):
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO signals (
            ticker, sentiment, sentiment_status, momentum, 
            momentum_status, volume_ratio, price_change_pct, score
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        signal.get("ticker"),
        signal.get("sentiment"),
        signal.get("sentiment_status"),
        signal.get("momentum"),
        signal.get("momentum_status"),
        signal.get("volume_ratio"),
        signal.get("price_change_pct"),
        signal.get("score")
    ))
    
    conn.commit()
    conn.close()

def load_all_signals():
    init_db()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM signals ORDER BY timestamp DESC")
    rows = cursor.fetchall()
    
    conn.close()
    return [dict(row) for row in rows]

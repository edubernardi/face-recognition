import sqlite3
import os
import numpy as np
from io import BytesIO

def init_db():
    conn = sqlite3.connect('face_recognition.sqlite')
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS images
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT NOT NULL,
                  filepath TEXT NOT NULL,
                  face_encoding BLOB,
                  upload_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

def add_image_record(username, filepath, face_encoding=None):
    conn = sqlite3.connect('face_recognition.sqlite')
    c = conn.cursor()
    
    c.execute("""INSERT INTO images (username, filepath, face_encoding) 
                 VALUES (?, ?, ?)""", 
              (username, filepath, face_encoding))
    conn.commit()
    conn.close()

def get_recent_images(limit=100):
    conn = sqlite3.connect('face_recognition.sqlite')
    c = conn.cursor()
    
    c.execute("""SELECT id, username, filepath, face_encoding 
                 FROM images 
                 ORDER BY upload_time DESC 
                 LIMIT ?""", (limit,))
    
    results = []
    for row in c.fetchall():
        face_encoding = np.frombuffer(row[3], dtype=np.float64) if row[3] else None
        results.append({
            'id': row[0],
            'username': row[1],
            'filepath': row[2],
            'face_encoding': face_encoding
        })
    
    conn.close()
    return results

def init_history_db():
    conn = sqlite3.connect('face_recognition.sqlite')
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS recognition_history
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  filepath TEXT NOT NULL,
                  matched_image_id INTEGER,
                  matched_username TEXT,
                  confidence REAL,
                  search_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY(matched_image_id) REFERENCES images(id))''')
    conn.commit()
    conn.close()

def add_history_record(filepath, matched_image_id=None, matched_username=None, confidence=None):
    conn = sqlite3.connect('face_recognition.sqlite')
    c = conn.cursor()
    
    c.execute("""INSERT INTO recognition_history 
                 (filepath, matched_image_id, matched_username, confidence) 
                 VALUES (?, ?, ?, ?)""", 
              (filepath, matched_image_id, matched_username, confidence))
    conn.commit()
    conn.close()

def get_all_face_encodings():
    conn = sqlite3.connect('face_recognition.sqlite')
    c = conn.cursor()
    
    c.execute("""SELECT id, username, face_encoding FROM images 
                 WHERE face_encoding IS NOT NULL""")
    
    results = []
    for row in c.fetchall():
        results.append({
            'id': row[0],
            'username': row[1],
            'face_encoding': np.frombuffer(row[2], dtype=np.float64)
        })
    
    conn.close()
    return results

def get_recognition_history():
    conn = sqlite3.connect('face_recognition.sqlite')
    c = conn.cursor()
    
    c.execute("""
        SELECT 
            h.filepath,
            h.matched_image_id,
            h.matched_username,
            h.confidence,
            h.search_time,
            i.filepath as matched_image_path
        FROM recognition_history h
        LEFT JOIN images i ON h.matched_image_id = i.id
        ORDER BY h.search_time DESC
        LIMIT 50
    """)
    
    history = []
    for row in c.fetchall():
        history.append({
            "search_image": row[0],
            "matched_image_id": row[1],
            "matched_username": row[2],
            "confidence": row[3],
            "timestamp": row[4],
            "matched_image_path": row[5]
        })
    conn.close()
    return history

init_db()
init_history_db()
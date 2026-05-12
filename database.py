import sqlite3
import datetime

DB_NAME = "liman.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Görevliler tablosu
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL
        )
    ''')

    # Kargolar / Sevkiyatlar tablosu
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS shipments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tracking_number TEXT UNIQUE NOT NULL,
            plate_number TEXT NOT NULL,
            entry_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            current_status TEXT NOT NULL,
            customs_cost REAL DEFAULT 0.0,
            vat_cost REAL DEFAULT 0.0,
            handling_cost REAL DEFAULT 0.0,
            is_archived INTEGER DEFAULT 0
        )
    ''')

    # Varsayılan Admin Kullanıcısı Oluşturma
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", ("admin", "admin123", "staff"))

    conn.commit()
    conn.close()

def get_connection():
    return sqlite3.connect(DB_NAME)

if __name__ == "__main__":
    init_db()
    print("Veritabanı başarıyla oluşturuldu.")

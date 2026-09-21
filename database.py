import os
import psycopg2
from psycopg2.extras import RealDictCursor
import sqlite3
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

def get_db():
    if DATABASE_URL:
        # Tambahkan connect_timeout agar tidak melempar error mendadak saat handshake SSL
        conn = psycopg2.connect(
            DATABASE_URL, 
            cursor_factory=RealDictCursor,
            sslmode="require",
            connect_timeout=10
        )
        return conn
    else:
        conn = sqlite3.connect("schedules.db")
        conn.row_factory = sqlite3.Row
        return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    
    # Deteksi apakah menggunakan PostgreSQL (Neon) atau SQLite
    is_postgres = bool(DATABASE_URL)

    if is_postgres:
        # Query khusus PostgreSQL
        query = """
        CREATE TABLE IF NOT EXISTS schedules (
            id SERIAL PRIMARY KEY,
            client_name VARCHAR(255) NOT NULL,
            whatsapp_number VARCHAR(50) NOT NULL,
            scheduled_time TIMESTAMP NOT NULL,
            control_number INT DEFAULT 1,
            message_content TEXT NOT NULL,
            status VARCHAR(20) DEFAULT 'PENDING' CHECK (status IN ('PENDING', 'SENT', 'FAILED', 'CANCELLED')),
            response_log TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
    else:
        # Query SQLite
        query = """
        CREATE TABLE IF NOT EXISTS schedules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_name TEXT NOT NULL,
            whatsapp_number TEXT NOT NULL,
            scheduled_time DATETIME NOT NULL,
            control_number INTEGER DEFAULT 1,
            message_content TEXT NOT NULL,
            status TEXT CHECK(status IN ('PENDING', 'SENT', 'FAILED', 'CANCELLED')) DEFAULT 'PENDING',
            response_log TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        """
    
    cursor.execute(query)
    conn.commit()
    cursor.close()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("Database Neon / SQLite berhasil diinisialisasi.")
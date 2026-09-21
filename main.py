from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from datetime import datetime
import database
import scheduler
import sqlite3
from fastapi import FastAPI, Depends, HTTPException
from database import get_db

app = FastAPI(title="WhatsApp Scheduler - Kontrol Nifas")

@app.on_event("startup")
def startup_event():
    database.init_db()
    scheduler.scheduler.start()
    scheduler.reload_pending_jobs()

@app.on_event("shutdown")
def shutdown_event():
    scheduler.scheduler.shutdown()

class ScheduleRequest(BaseModel):
    client_name: str
    whatsapp_number: str
    scheduled_time: str
    control_number: int  # Pilihan 1, 2, atau 3

@app.post("/api/schedule")
def create_schedule(req: ScheduleRequest):
    try:
        run_time = datetime.fromisoformat(req.scheduled_time)
    except ValueError:
        raise HTTPException(status_code=400, detail="Format tanggal/waktu tidak valid. Gunakan YYYY-MM-DDTHH:MM")

    if run_time <= datetime.now():
        raise HTTPException(status_code=400, detail="Waktu jadwal harus di masa depan.")

    if req.control_number not in [1, 2, 3]:
        raise HTTPException(status_code=400, detail="Pilihan kontrol nifas hanya 1, 2, atau 3.")

    # Otomatisasi isi pesan berdasarkan input
    message_content = (
        f"Hi ibu {req.client_name}, besok ada jadwal kontrol nifas ke-{req.control_number}. "
        f"Mohon untuk hadir tepat waktu ya. Terima kasih."
    )

    conn = database.get_db()
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO schedules (client_name, whatsapp_number, scheduled_time, control_number, message_content)
           VALUES (?, ?, ?, ?, ?)""",
        (req.client_name, req.whatsapp_number, run_time.isoformat(), req.control_number, message_content)
    )
    schedule_id = cursor.lastrowid
    conn.commit()
    conn.close()

    # Daftarkan ke scheduler
    scheduler.schedule_job(schedule_id, run_time)

    return {"status": "success", "id": schedule_id, "message": "Jadwal kontrol nifas berhasil disimpan"}

@app.get("/api/schedules")
def list_schedules():
    conn = database.get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM schedules ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def read_root():
    return FileResponse("static/index.html")

@app.delete("/api/schedule/{schedule_id}")
def cancel_schedule(schedule_id: int, db: sqlite3.Connection = Depends(database.get_db)):
    cursor = db.cursor()
    
    cursor.execute("SELECT status FROM schedules WHERE id = %s", (schedule_id,))
    row = cursor.fetchone()
    
    if not row:
        raise HTTPException(status_code=404, detail="Jadwal tidak ditemukan")
    
    if row["status"] != "PENDING":
        raise HTTPException(status_code=400, detail="Hanya jadwal berstatus PENDING yang dapat dibatalkan")
    
    # 1. Ubah status di database
    cursor.execute("UPDATE schedules SET status = 'CANCELLED', response_log = 'Dibatalkan oleh pengguna' WHERE id = ?", (schedule_id,))
    db.commit()
    
    # 2. Hapus job dari APScheduler memori
    scheduler.cancel_job(schedule_id)
    
    return {"status": "success", "message": "Jadwal berhasil dibatalkan"}
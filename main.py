from datetime import datetime
from fastapi import FastAPI, HTTPException, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import database
import scheduler

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

    message_content = (
        f"Hi ibu {req.client_name}, besok ada jadwal kontrol nifas ke-{req.control_number}. "
        f"Mohon untuk hadir tepat waktu ya. Terima kasih."
    )

    conn = database.get_db()
    cursor = conn.cursor()
    
    try:
        # Tambahkan RETURNING id agar PostgreSQL mengembalikan ID baris baru
        cursor.execute(
            """INSERT INTO schedules (client_name, whatsapp_number, scheduled_time, control_number, message_content)
               VALUES (%s, %s, %s, %s, %s)
               RETURNING id""",
            (req.client_name, req.whatsapp_number, run_time.isoformat(), req.control_number, message_content)
        )
        
        # Samakan nama variabel menjadi schedule_id
        schedule_id = cursor.fetchone()['id']
        conn.commit()

        # Daftarkan ke APScheduler
        scheduler.schedule_job(schedule_id, run_time)

        return {"status": "success", "id": schedule_id, "message": "Jadwal kontrol nifas berhasil disimpan"}

    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        cursor.close()
        conn.close()

@app.get("/api/schedules")
def list_schedules():
    conn = database.get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM schedules ORDER BY created_at DESC")
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        cursor.close()
        conn.close()

@app.delete("/api/schedule/{schedule_id}")
def cancel_schedule(schedule_id: int):
    conn = database.get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT status FROM schedules WHERE id = %s", (schedule_id,))
        row = cursor.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="Jadwal tidak ditemukan")
        
        if row["status"] != "PENDING":
            raise HTTPException(status_code=400, detail="Hanya jadwal berstatus PENDING yang dapat dibatalkan")
        
        # Ubah '?' menjadi '%s'
        cursor.execute(
            "UPDATE schedules SET status = 'CANCELLED', response_log = 'Dibatalkan oleh pengguna' WHERE id = %s", 
            (schedule_id,)
        )
        conn.commit()
        
        # Hapus dari memori scheduler
        scheduler.cancel_job(schedule_id)
        
        return {"status": "success", "message": "Jadwal berhasil dibatalkan"}
        
    except Exception as e:
        conn.rollback()
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def read_root():
    return FileResponse("static/index.html")
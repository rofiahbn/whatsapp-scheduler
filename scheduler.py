from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.date import DateTrigger
from datetime import datetime
import inspect
import database
import whatsapp

scheduler = BackgroundScheduler()

def _get_connection():
    """Helper internal untuk mengambil objek connection dari database.py secara aman."""
    db_obj = database.get_db()
    # Jika get_db() adalah generator (pakai yield)
    if inspect.isgenerator(db_obj):
        return next(db_obj)
    # Jika get_db() fungsi biasa (pakai return)
    return db_obj

def process_scheduled_message(schedule_id: int):
    """Callback function triggered by APScheduler at the target time."""
    print(f"\n[SCHEDULER EXECUTING] Memproses Job ID: {schedule_id}")
    
    conn = _get_connection()
    cursor = conn.cursor()
    
    try:
        # Gunakan %s untuk PostgreSQL Neon
        cursor.execute("SELECT * FROM schedules WHERE id = %s", (schedule_id,))
        row = cursor.fetchone()
        
        if not row:
            print(f"[SCHEDULER ERROR] Data ID {schedule_id} tidak ditemukan di database.")
            return

        # GUARD CHECK: Jika status bukan PENDING (misal CANCELLED), batalkan pengiriman pesan
        if row["status"] != "PENDING":
            print(f"[SCHEDULER SKIPPED] Job ID {schedule_id} dibatalkan karena status = '{row['status']}'.")
            return

        # Panggil fungsi pengirim WhatsApp
        success, log_msg = whatsapp.send_whatsapp_message(
            to_number=row["whatsapp_number"],
            message=row["message_content"]
        )
        
        print(f"[SCHEDULER RESULT] ID {schedule_id} | Status: {success} | Log: {log_msg}")

        # Update Status
        new_status = "SENT" if success else "FAILED"
        cursor.execute(
            "UPDATE schedules SET status = %s, response_log = %s WHERE id = %s",
            (new_status, log_msg, schedule_id)
        )
        conn.commit()
    finally:
        conn.close()

def schedule_job(schedule_id: int, run_time: datetime):
    """Register a new job to APScheduler."""
    scheduler.add_job(
        func=process_scheduled_message,
        trigger=DateTrigger(run_date=run_time),
        args=[schedule_id],
        id=str(schedule_id),
        replace_existing=True,
        misfire_grace_time=60
    )
    print(f"[SCHEDULER] Job ID {schedule_id} berhasil didaftarkan untuk jam: {run_time}")

def cancel_job(schedule_id: int):
    """Remove a scheduled job from APScheduler memory."""
    try:
        scheduler.remove_job(str(schedule_id))
        print(f"[SCHEDULER] Job ID {schedule_id} berhasil dihapus dari memori scheduler.")
    except Exception as e:
        print(f"[SCHEDULER WARNING] Job ID {schedule_id} tidak ditemukan di memori scheduler: {e}")

def reload_pending_jobs():
    """Load unexecuted jobs from SQLite into APScheduler on server startup."""
    conn = _get_connection()
    cursor = conn.cursor()
    now = datetime.now()
    
    try:
        cursor.execute("SELECT id, scheduled_time FROM schedules WHERE status = 'PENDING'")
        rows = cursor.fetchall()
        
        for row in rows:
            try:
                job_time_str = str(row["scheduled_time"]).replace("Z", "")
                job_time = datetime.fromisoformat(job_time_str)
                
                if job_time >= now:
                    schedule_job(row["id"], job_time)
                else:
                    print(f"[SCHEDULER] Job ID {row['id']} terlewat. Jam Target: {job_time}, Jam Sekarang: {now}")
                    cursor.execute(
                        "UPDATE schedules SET status = 'FAILED', response_log = 'Missed execution time' WHERE id = %s",
                        (row["id"],)
                    )
            except Exception as e:
                print(f"[SCHEDULER ERROR] Format tanggal salah pada ID {row['id']}: {str(e)}")

        conn.commit()
    finally:
        conn.close()
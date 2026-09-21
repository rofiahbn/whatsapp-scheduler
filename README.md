# 🩺 SIMONIKA - WhatsApp Scheduler Kontrol Nifas

**SIMONIKA** adalah aplikasi berbasis web yang dibangun menggunakan **FastAPI** dan **APScheduler** untuk menjadwalkan dan mengirimkan pesan pengingat jadwal kontrol nifas secara otomatis ke WhatsApp pasien melalui **Fonnte API**. Aplikasi ini menggunakan database **Neon PostgreSQL** dan dirancang agar siap di-deploy ke **Railway**.

---

## 🚀 Fitur Utama

- **Otomatisasi Pesan WhatsApp:** Mengirim pesan pengingat kontrol nifas (Kontrol ke-1, ke-2, dan ke-3) tepat waktu sesuai jadwal yang ditentukan.
- **Job Persistence (PostgreSQL):** Jadwal yang berstatus `PENDING` akan otomatis dimuat ulang ke dalam memori scheduler jika server mengalami *restart* atau *redeploy*.
- **Timezone-Aware (`Asia/Jakarta`):** Memastikan eksekusi waktu pengiriman akurat sesuai Waktu Indonesia Barat (WIB).
- **Auto Phone Formatter:** Otomatis membersihkan dan mengubah format nomor HP (seperti `08...` atau `+62...`) menjadi standar internasional (`62...`).
- **Manajemen Status & Log:** Melacak status pesan (`PENDING`, `SENT`, `FAILED`, `CANCELLED`) beserta *response log* dari API Fonnte.

---

## 🛠️ Tech Stack

- **Backend:** Python 3.13, FastAPI, Uvicorn
- **Database:** Neon PostgreSQL (via `psycopg2` / `httpx`)
- **Scheduler:** APScheduler (BackgroundScheduler)
- **WhatsApp Gateway:** Fonnte API
- **Deployment:** Railway.app

---

## ⚙️ Environment Variables

Buat file `.env` di root folder project untuk pengembangan lokal dengan format berikut:

```env
DATABASE_URL=postgresql://user:password@host/database?sslmode=require
FONNTE_TOKEN=your_fonnte_api_token_here
TEST_MODE=false

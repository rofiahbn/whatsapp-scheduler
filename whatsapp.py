import os
import httpx
from dotenv import load_dotenv

load_dotenv()

FONNTE_TOKEN = os.getenv("FONNTE_TOKEN")
# Ubah "true" menjadi "false" di bagian belakang
TEST_MODE = os.getenv("TEST_MODE", "false").lower() == "true"

def send_whatsapp_message(to_number: str, message: str) -> tuple[bool, str]:
    """
    Mengirim pesan WhatsApp menggunakan API Fonnte via HP Pribadi.
    """
    # Bersihkan nomor dari karakter selain angka (+, -, spasi)
    clean_number = "".join(filter(str.isdigit, to_number))
    
    # Ubah format awal 08xx menjadi 628xx secara otomatis
    if clean_number.startswith("0"):
        clean_number = "62" + clean_number[1:]

    if TEST_MODE:
        print(f"\n--- [TEST MODE ACTIVE] ---")
        print(f"Ke: {clean_number}")
        print(f"Pesan: {message}")
        print(f"---------------------------\n")
        return True, "TEST_MODE: Pesan berhasil disimulasikan."

    url = "https://api.fonnte.com/send"
    headers = {
        "Authorization": FONNTE_TOKEN
    }
    payload = {
        "target": clean_number,
        "message": message,
        "countryCode": "62"
    }

    try:
        response = httpx.post(url, data=payload, headers=headers, timeout=10.0)
        data = response.json()
        
        # Fonnte mengembalikan status: True jika berhasil
        if data.get("status") == True:
            return True, "Berhasil terkirim via Fonnte"
        else:
            reason = data.get("reason", response.text)
            return False, f"Fonnte Error: {reason}"
            
    except Exception as e:
        return False, f"Koneksi Error: {str(e)}"
import os
import asyncio
import yfinance as yf
from datetime import datetime, timezone
from supabase import create_client, Client
from dotenv import load_dotenv
import logging

load_dotenv()

supabase_url = os.environ.get("SUPABASE_URL")
supabase_key = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(supabase_url, supabase_key)

logging.getLogger('yfinance').setLevel(logging.CRITICAL)

def dinamik_sembol_cozucu(sembol: str):
    """Kullanıcının girdiği sembolün gerçek piyasa karşılığını akıllıca bulur."""
    sembol = sembol.upper().strip()
    
    # Eğer zaten doğru formatta geldiyse (.IS veya -USD varsa) direkt onu kullan
    if sembol.endswith(".IS") or "-USD" in sembol:
        return sembol
        
    varyasyonlar = []
    bilinen_kriptolar = [
        "BTC", "ETH", "USDT", "BNB", "SOL", "XRP", "ADA", "AVAX", 
        "DOGE", "DOT", "LINK", "TRX", "SHIB", "ETC", "LTC", "BCH"
    ]
    
    # AKILLI TAHMİN ALGORİTMASI
    if sembol in bilinen_kriptolar:
        # Kriptoysa önce -USD denesin
        varyasyonlar = [f"{sembol}-USD", sembol]
    else:
        # Değilse muhtemelen Türk Hissesidir, önce .IS denesin, sonra Amerikan denesin
        varyasyonlar = [f"{sembol}.IS", sembol, f"{sembol}-USD"]
    
    for denenen in varyasyonlar:
        try:
            varlik = yf.Ticker(denenen)
            fiyat = varlik.fast_info['lastPrice'] 
            if fiyat > 0:
                return denenen # Doğruyu ilk seferde bulduk, dön!
        except Exception:
            pass # Gevezelik yapma, sessizce diğerine geç
            
    return sembol

def alarmlari_kontrol_et():
    """Arka planda çalışıp fiyatları kontrol eden ve tetiği çeken fonksiyon."""
    try:
        yanit = supabase.table("alarmlar").select("*").eq("aktif_mi", True).eq("durum", "bekliyor").execute()
        bekleyen_alarmlar = yanit.data

        if not bekleyen_alarmlar:
            return {"durum": "bilgi", "mesaj": "Bekleyen alarm yok."}

        tetiklenen_sayisi = 0

        for alarm in bekleyen_alarmlar:
            orijinal_sembol = alarm["varlik_sembolu"]
            ust_limit = alarm.get("ust_limit")
            alt_limit = alarm.get("alt_limit")

            # --- DİNAMİK ÇÖZÜCÜYÜ KULLAN ---
            dogru_sembol = dinamik_sembol_cozucu(orijinal_sembol)
                
            varlik = yf.Ticker(dogru_sembol)
            anlik_fiyat = varlik.fast_info['lastPrice']

            tetiklendi_mi = False

            if ust_limit and anlik_fiyat >= ust_limit:
                tetiklendi_mi = True
            elif alt_limit and anlik_fiyat <= alt_limit:
                tetiklendi_mi = True

            if tetiklendi_mi:
                simdi = datetime.now(timezone.utc).isoformat()
                
                supabase.table("alarmlar").update({
                    "tetiklendi_mi": True,
                    "aktif_mi": False,
                    "durum": "tetiklendi",
                    "tetiklenme_fiyati": round(anlik_fiyat, 2),
                    "tetiklenme_zamani": simdi
                }).eq("id", alarm["id"]).execute()
                
                tetiklenen_sayisi += 1
                print(f"🔔 ALARM TETİKLENDİ: {orijinal_sembol} ({dogru_sembol}) -> Fiyat: {anlik_fiyat}")

        return {"durum": "başarılı", "mesaj": f"{tetiklenen_sayisi} adet alarm tetiklendi."}

    except Exception as e:
        print(f"Alarm Motoru Hatası: {e}")
        return {"durum": "hata", "mesaj": str(e)}

async def fiyat_kontrol_dongusu():
    print("🚀 Arka Plan Alarm Motoru Başlatıldı! (60 saniyede bir kontrol edilecek)")
    while True:
        try:
            alarmlari_kontrol_et()
        except Exception as e:
            print(f"Alarm Döngüsü Hatası: {e}")
        await asyncio.sleep(60)
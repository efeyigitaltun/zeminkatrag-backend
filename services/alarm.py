import os
import asyncio
import yfinance as yf
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

# Supabase Bağlantısı
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

async def fiyat_kontrol_dongusu():
    """
    Sunucu çalıştığı sürece arka planda sonsuz bir döngüde çalışır.
    Aktif alarmları veritabanından çeker, yfinance ile güncel fiyatlara bakar.
    Hedef tutarsa alarmı 'tetiklendi' olarak günceller.
    """
    print("🚀 Arka Plan Alarm Motoru Başlatıldı! Gözler piyasada...")
    
    while True:
        try:
            # 1. Supabase'den sadece 'aktif_mi = true' olan alarmları çek
            response = supabase.table("alarmlar").select("*").eq("aktif_mi", True).execute()
            alarmlar = response.data
            
            if not alarmlar:
                # Aktif alarm yoksa sistemi yorma, 60 saniye uyu ve tekrar bak
                await asyncio.sleep(60)
                continue
                
            # 2. Aynı hisse için yfinance'e 10 kere istek atmamak için sembolleri tekilleştir
            semboller = list(set([alarm["varlik_sembolu"] for alarm in alarmlar]))
            
            fiyatlar = {}
            for sembol in semboller:
                try:
                    varlik = yf.Ticker(sembol)
                    # fast_info anlık fiyat çekmek için en hızlı yöntemdir
                    guncel_fiyat = varlik.fast_info['lastPrice'] 
                    fiyatlar[sembol] = guncel_fiyat
                except Exception:
                    continue # Bir hissede hata olursa diğerlerine geç
                    
            # 3. Çekilen güncel fiyatlar ile kullanıcının alarmlarını kıyasla
            for alarm in alarmlar:
                sembol = alarm["varlik_sembolu"]
                fiyat = fiyatlar.get(sembol)
                
                if not fiyat:
                    continue
                    
                tetiklendi = False
                mesaj = ""
                
                # Yukarı kırılım kontrolü (Örn: BTC 70 bini geçerse)
                if alarm["ust_limit"] and fiyat >= alarm["ust_limit"]:
                    tetiklendi = True
                    mesaj = f"YUKARI KIRILIM: {sembol} hedeflenen {alarm['ust_limit']} seviyesini geçti! (Anlık: {fiyat:.2f})"
                    
                # Aşağı kırılım kontrolü (Örn: BTC 60 binin altına düşerse)
                elif alarm["alt_limit"] and fiyat <= alarm["alt_limit"]:
                    tetiklendi = True
                    mesaj = f"AŞAĞI KIRILIM: {sembol} hedeflenen {alarm['alt_limit']} seviyesinin altına düştü! (Anlık: {fiyat:.2f})"
                    
                # 4. Eğer alarm koşulu sağlandıysa veritabanını güncelle ve bildir
                if tetiklendi:
                    print(f"🔔 [ALARM TETİKLENDİ] {mesaj}")
                    
                    # Supabase'de alarmı kapat ki sürekli ötmesin
                    supabase.table("alarmlar").update({
                        "tetiklendi_mi": True,
                        "aktif_mi": False
                    }).eq("id", alarm["id"]).execute()
                    
        except Exception as e:
            print(f"Alarm Motoru Hatası: {e}")
            
        # Döngüyü 60 saniye beklet (Sunucu çökmesin diye çok önemli)
        await asyncio.sleep(60)
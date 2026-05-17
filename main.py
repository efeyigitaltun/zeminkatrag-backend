from fastapi import FastAPI, HTTPException
import os
from dotenv import load_dotenv
from supabase import create_client, Client
from services.rag import finansal_haberleri_vektorle, yapay_zeka_kocuna_sor, yerel_piyasa_ve_halka_arz_ogret
from services.finance import get_live_price # Yazdığımız servisi içeri aldık
from services.simulasyon import finansal_simulasyon_yap

# .env dosyasındaki şifreleri sisteme yükle
load_dotenv()

# FastAPI uygulamasını başlat
app = FastAPI(title="ZeminKatRAG API")

# Supabase Bağlantısı
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

@app.get("/")
def read_root():
    return {"mesaj": "Makine Dairesi Çalışıyor! ZeminKatRAG API Ayakta."}

@app.get("/db-test")
def test_db():
    response = supabase.table("alarmlar").select("*").limit(1).execute()
    return {"durum": "Başarılı", "veri": response.data}

# YENİ EKLENEN API UCU
@app.get("/api/fiyat/{sembol}")
def fiyat_getir(sembol: str):
    fiyat = get_live_price(sembol)
    
    if fiyat is None:
        # Eğer yfinance sembolü bulamazsa 404 hatası dön
        raise HTTPException(status_code=404, detail=f"{sembol} için veri bulunamadı.")
    
    return {
        "sembol": sembol.upper(), 
        "fiyat": fiyat,
        "kaynak": "Yahoo Finance"
    }

# RAG VERİ TABANINI GÜNCELLEME UCU
@app.get("/api/rag/haber-guncelle/{sembol}")
def haber_guncelle(sembol: str):
    sonuc = finansal_haberleri_vektorle(sembol)
    return sonuc

# YAPAY ZEKA KOÇU CHAT UCU
from pydantic import BaseModel

# Kullanıcıdan gelecek verinin yapısı (Sadece 'soru' text'i gelecek)
class SoruModeli(BaseModel):
    soru: str
    risk_profili: str = "orta" # Varsayılan olarak orta risk seçtik

@app.post("/api/chat")
def chat_ile_sor(veri: SoruModeli):
    # Kullanıcıdan gelen risk profilini de fonksiyona paslıyoruz
    sonuc = yapay_zeka_kocuna_sor(veri.soru, veri.risk_profili)
    return sonuc

# YEREL PİYASA VE HALKA ARZ GÜNCELLEME UCU
@app.get("/api/rag/yerel-gundem-guncelle")
def yerel_gundem_guncelle():
    sonuc = yerel_piyasa_ve_halka_arz_ogret()
    return sonuc

# SİMÜLASYON AJANI UCU
class SimulasyonModeli(BaseModel):
    aylik_gelir: float
    aylik_gider: float
    hedef: str
    risk_profili: str = "orta"

@app.post("/api/simulasyon")
def simulasyon_calistir(veri: SimulasyonModeli):
    sonuc = finansal_simulasyon_yap(
        veri.aylik_gelir, 
        veri.aylik_gider, 
        veri.hedef, 
        veri.risk_profili
    )
    return sonuc
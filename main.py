from fastapi import FastAPI
import os
from dotenv import load_dotenv
from supabase import create_client, Client

# .env dosyasındaki şifreleri sisteme yükle
load_dotenv()

# FastAPI uygulamasını başlat
app = FastAPI(title="CüzdanRAG API")

# Supabase Bağlantısı
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

@app.get("/")
def read_root():
    return {"mesaj": "Makine Dairesi Çalışıyor! CüzdanRAG API Ayakta."}

@app.get("/db-test")
def test_db():
    # Supabase'e bağlanabiliyor muyuz test edelim
    response = supabase.table("alarmlar").select("*").limit(1).execute()
    return {"durum": "Başarılı", "veri": response.data}
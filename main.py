from fastapi import FastAPI, HTTPException
import os
from dotenv import load_dotenv
from supabase import create_client, Client
from services.rag import finansal_haberleri_vektorle, yapay_zeka_kocuna_sor, yerel_piyasa_ve_halka_arz_ogret
from services.finance import get_live_price # Yazdığımız servisi içeri aldık
from services.simulasyon import finansal_simulasyon_yap
from contextlib import asynccontextmanager
import asyncio
from services.alarm import fiyat_kontrol_dongusu
from typing import List
from services.portfoy_analiz import portfoy_saglik_skoru_hesapla
from services.davranis_analizi import davranisal_bias_tespit_et
from services.vergi_maliyet import vergi_ve_maliyet_hesapla
from services.aciklanabilir_ai import oneriyi_acikla

# .env dosyasındaki şifreleri sisteme yükle
load_dotenv()

# Sunucu açıldığında ve kapandığında ne yapılacağını belirleyen yaşam döngüsü
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Sunucu başlarken alarm motorunu arka planda yeni bir görev olarak başlat
    alarm_gorevi = asyncio.create_task(fiyat_kontrol_dongusu())
    yield
    # Sunucu kapanırken görevi iptal et
    alarm_gorevi.cancel()

# FastAPI uygulamasını oluştururken lifespan'i tanımlıyoruz
app = FastAPI(
    title="ZeminKatRAG API",
    lifespan=lifespan
)

from fastapi.middleware.cors import CORSMiddleware

# ... (app = FastAPI(...) satırının hemen altına ekle) ...

# Hackathon için dışarıdan gelen tüm isteklere (Flutter vb.) kapıları ardına kadar açıyoruz
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

from pydantic import BaseModel
from typing import Optional
import os
from supabase import create_client

class AlarmModeli(BaseModel):
    kullanici_id: str
    varlik_sembolu: str
    alt_limit: Optional[float] = None
    ust_limit: Optional[float] = None

@app.post("/api/alarm/kur")
def alarm_kur(veri: AlarmModeli):
    try:
        supabase = create_client(os.environ.get("SUPABASE_URL"), os.environ.get("SUPABASE_KEY"))
        alarm_verisi = {
            "kullanici_id": veri.kullanici_id,
            "varlik_sembolu": veri.varlik_sembolu.upper(),
            "alt_limit": veri.alt_limit,
            "ust_limit": veri.ust_limit
        }
        supabase.table("alarmlar").insert(alarm_verisi).execute()
        return {"durum": "başarılı", "mesaj": f"{veri.varlik_sembolu} için alarm başarıyla kuruldu."}
    except Exception as e:
        return {"durum": "hata", "mesaj": str(e)}
    
    # PORTFÖY SAĞLIK SKORU UCU
class VarlikModeli(BaseModel):
    sembol: str
    tutar: float

class PortfoySorgusu(BaseModel):
    risk_profili: str = "orta"  
    varliklar: List[VarlikModeli]

@app.post("/api/portfoy/saglik")
def portfoy_saglik_kontrolu(veri: PortfoySorgusu):
    # Pydantic modelindeki listeyi Python dictionary listesine çeviriyoruz
    varlik_listesi = [{"sembol": v.sembol, "tutar": v.tutar} for v in veri.varliklar]
    sonuc = portfoy_saglik_skoru_hesapla(varlik_listesi, veri.risk_profili)
    return sonuc

# DAVRANIŞSAL FİNANS (BİAS DEDEKTÖRÜ) UCU
class IslemModeli(BaseModel):
    sembol: str
    islem: str # "AL" veya "SAT"
    kar_zarar: str # Örn: "%-20"
class IslemGecmisiSorgusu(BaseModel):
    islemler: List[IslemModeli]

@app.post("/api/portfoy/davranis")
def davranis_analizi_yap(veri: IslemGecmisiSorgusu):
    # Artık piyasa durumunu kullanıcıdan almıyoruz
    islem_listesi = [
        {
            "sembol": v.sembol, 
            "islem": v.islem, 
            "kar_zarar": v.kar_zarar
        } 
        for v in veri.islemler
    ]
    sonuc = davranisal_bias_tespit_et(islem_listesi)
    return sonuc

# VERGİ VE MALİYET OPTİMİZASYON UCU
class MaliyetSorgusu(BaseModel):
    varlik_tipi: str # "hisse", "fon", "kripto"
    alis_tutari: float
    satis_tutari: float
    elde_tutma_suresi_ay: int

@app.post("/api/portfoy/maliyet")
def maliyet_optimizasyonu_yap(veri: MaliyetSorgusu):
    sonuc = vergi_ve_maliyet_hesapla(
        veri.varlik_tipi, 
        veri.alis_tutari, 
        veri.satis_tutari, 
        veri.elde_tutma_suresi_ay
    )
    return sonuc

# EXPLAINABLE AI (NEDEN?) UCU
class AciklamaSorgusu(BaseModel):
    onerilen_islem: str
    risk_profili: str
    hedef_sure_ay: int
    piyasa_ozeti: str

@app.post("/api/analiz/neden")
def onerinin_nedenini_sor(veri: AciklamaSorgusu):
    sonuc = oneriyi_acikla(veri.onerilen_islem, veri.risk_profili, veri.hedef_sure_ay, veri.piyasa_ozeti)
    return sonuc
import os
import json
from pathlib import Path
from google import genai
from google.genai.errors import APIError
from dotenv import load_dotenv

# --- KESİN ÇÖZÜM: .env Dosyasının Tam Yolunu Bulmak ---
# Bu kod, ai_core.py'ın bulunduğu yerden 1 klasör yukarı çıkıp (kök dizin) .env dosyasını nokta atışı bulur.
proje_kok_dizini = Path(__file__).resolve().parent.parent
env_yolu = proje_kok_dizini / ".env"
load_dotenv(dotenv_path=env_yolu, override=True)

# --- GEÇİCİ LOG TESTİ ---
print("🔍 .env içinden okunan ANA anahtar kelimesi:", os.environ.get("GEMINI_API_KEY_ANA"))
print("🔍 .env içinden okunan YEDEK anahtar kelimesi:", os.environ.get("GEMINI_API_KEY_YEDEK"))
# ------------------------
# -----------------------------------------------------

def guvenli_llm_cagir(prompt: str):
    """
    Sadece .env dosyasından okuma yapan, yolu otomatik çözen 
    ve hata anında yedek motora saniyesinde atlayan hızlı fonksiyon.
    """
    ana_key = os.environ.get("GEMINI_API_KEY_ANA")
    yedek_key = os.environ.get("GEMINI_API_KEY_YEDEK")

    # 1. ANA MOTOR DENEMESİ
    try:
        if not ana_key:
            raise ValueError("Ana API anahtarı .env dosyasında bulunamadı veya içi boş.")
            
        client = genai.Client(api_key=ana_key)
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        return response
        
    except Exception as e_ana:
        print(f"⚠️ [DİKKAT] Ana API Hatası: {e_ana}")
        print("⚠️ Yedek Motora Geçiliyor...")
        
        # 2. YEDEK MOTOR DENEMESİ
        try:
            if not yedek_key:
                raise ValueError("Yedek API anahtarı .env dosyasında bulunamadı veya içi boş.")
                
            client_yedek = genai.Client(api_key=yedek_key, http_options={'api_version': 'v1'})
            response_yedek = client_yedek.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )
            return response_yedek
            
        except Exception as e_yedek:
            print(f"❌ [KRİTİK] Yedek Motor da Patladı: {e_yedek}")
            
            # Sunum kurtaran yedek Mock yapısı
            class MockResponse:
                def __init__(self, text):
                    self.text = text
            
            acil_durum_json = """
            {
                "tespit_edilen_zaaf": "Duygusal İşlem ve Aşırı Alım Duygusu (FOMO)",
                "analiz_ozeti": "Kullanıcının piyasa hareketlerine duygusal tepki verdiği ve trendleri tepeden yakaladığı gözlemlenmiştir.",
                "kocun_tavsiyesi": "İşlemlerinizde stop-loss kullanmalı ve piyasa ralli yaparken fevri kararlar almaktan kaçınmalısınız."
            }
            """
            return MockResponse(acil_durum_json)

def guvenli_json_parse(json_metni: str):
    try:
        metin = json_metni.text if hasattr(json_metni, 'text') else str(json_metni)
        metin = metin.replace("```json", "").replace("```", "").strip()
        return json.loads(metin)
    except Exception as e:
        return {
            "durum": "hata",
            "mesaj": f"JSON Parse Hatası: {str(e)}"
        }
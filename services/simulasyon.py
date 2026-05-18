import os
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv

load_dotenv()

# Gemini Modeli Bağlantısı
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash", 
    google_api_key=os.environ.get("GEMINI_API_KEY_ANA")
)

def finansal_simulasyon_yap(aylik_gelir: float, aylik_gider: float, hedef: str, risk_profili: str = "orta"):
    """
    Kullanıcının gelir-gider durumuna göre hedefine ulaşması için 
    matematiksel bir senaryo ve strateji çizer.
    """
    try:
        tasarruf_potansiyeli = aylik_gelir - aylik_gider
        
        # Simülasyon ajanına özel, matematik ve strateji odaklı prompt
        prompt = f"""Sen ZeminKatRAG uygulamasının profesyonel 'Finansal Simülasyon Ajanısın'. 
        Kullanıcının verilerine dayanarak matematiksel bir yol haritası ve simülasyon çizeceksin.

        [KULLANICI VERİLERİ]
        - Aylık Gelir: {aylik_gelir} TL
        - Aylık Gider: {aylik_gider} TL
        - Mevcut Tasarruf Potansiyeli: {tasarruf_potansiyeli} TL
        - Ulaşmak İstediği Hedef: {hedef}
        - Risk Profili: {risk_profili.upper()}

        [GÖREVLERİN]
        1. Matematiksel Projeksiyon: Mevcut tasarruf ile hedefe ne kadar sürede ulaşılacağını hesapla.
        2. Alternatif Senaryo (Optimizasyon): Kullanıcıya giderlerini %5 veya %10 oranında kısması durumunda hedefine ne kadar daha erken ulaşacağını sayılarla göster (dinamik senaryo).
        3. Risk profiline uygun değerlendirme: Tasarruf edilen bu paranın enflasyon karşısında erimemesi için kullanıcının risk profiline uygun varlık sınıfları (mevduat, para piyasası fonu, altın, düşük/yüksek riskli fonlar vb.) öner.
        4. Motive edici ve basit bir dil kullan. Analojilerle anlat.
        5. Her zamanki gibi doğrudan hisse/coin tavsiyesi vermeden yasal sınırlar içinde kal.
        """
        
        cevap = llm.invoke(prompt)
        
        return {
            "durum": "başarılı", 
            "simulasyon_sonucu": cevap.content,
            "hesaplanan_tasarruf": tasarruf_potansiyeli
        }
        
    except Exception as e:
        print(f"Simülasyon Hatası: {e}")
        return {"durum": "hata", "mesaj": str(e)}
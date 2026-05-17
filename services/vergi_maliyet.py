import os
import json
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv

load_dotenv()

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash", 
    google_api_key=os.environ.get("GEMINI_API_KEY")
)

def vergi_ve_maliyet_hesapla(varlik_tipi: str, alis_tutari: float, satis_tutari: float, elde_tutma_suresi_ay: int):
    """
    Türkiye şartlarındaki kaba vergi, komisyon ve fon giderlerini hesaplar.
    varlik_tipi: "hisse", "fon" veya "kripto"
    """
    try:
        brut_kar = satis_tutari - alis_tutari
        getiri_orani = (brut_kar / alis_tutari) * 100

        komisyon = 0
        vergi = 0
        fon_gideri = 0

        # Basitleştirilmiş Türkiye Vergi/Maliyet Senaryosu
        if varlik_tipi.lower() == "hisse":
            komisyon = (alis_tutari + satis_tutari) * 0.002 # Ortalama binde 2 banka/aracı kurum komisyonu
            vergi = 0 # BIST hisselerinde genelde stopaj %0'dır
        
        elif varlik_tipi.lower() == "fon":
            # Yıllık ortalama %2.5 fon yönetim gideri (TER) kesintisi
            fon_gideri = alis_tutari * 0.025 * (elde_tutma_suresi_ay / 12)
            # Kar üzerinden %10 stopaj (Hisse yoğun fonlar hariç genel TEFAS varsayımı)
            if brut_kar > 0:
                vergi = brut_kar * 0.10
        
        elif varlik_tipi.lower() == "kripto":
            komisyon = (alis_tutari + satis_tutari) * 0.002 # Kripto borsa komisyonu (Maker/Taker kaba hesap)
            vergi = 0 # Mevcut TR regülasyonunda sıfır kabul ediliyor

        toplam_kesinti = komisyon + vergi + fon_gideri
        net_kar = brut_kar - toplam_kesinti

        # Gemini'a sadece bu kesintileri yorumlama görevi veriyoruz
        prompt = f"""Sen ZeminKatRAG'in Vergi ve Maliyet Optimizasyon uzmanısın.
        Kullanıcı bir işlem yaptı veya simüle ediyor. Ona brüt kârın 'gizli maliyetlerle' nasıl eridiğini acımasızca göster.

        [MATEMATİKSEL VERİLER]
        - Varlık Tipi: {varlik_tipi.upper()}
        - Brüt Kâr: {brut_kar:.2f} TL (%{getiri_orani:.2f})
        - Toplam Gizli Kesinti (Vergi+Komisyon+Yönetim Ücreti): {toplam_kesinti:.2f} TL
        - Eline Geçecek Net Kâr: {net_kar:.2f} TL

        Lütfen SADECE aşağıdaki yapıda geçerli bir JSON formatında cevap ver:
        {{
            "gizli_maliyet_analizi": "Brüt kar ile net kar arasındaki farkı anlatan kısa yorum. Kazandığını sanarken ne kadarını sisteme bıraktı?",
            "optimizasyon_tavsiyesi": "Maliyetleri düşürmek için taktik. (Örn: Stopajsız hisse yoğun fonlara geçmek veya az işlem yapıp komisyon ödememek)"
        }}
        """

        cevap = llm.invoke(prompt)
        temiz_json = cevap.content.replace("```json", "").replace("```", "").strip()
        yapay_zeka_yorumu = json.loads(temiz_json)

        return {
            "durum": "başarılı",
            "finansal_tablo": {
                "brut_kar_tl": round(brut_kar, 2),
                "vergi_stopaj_tl": round(vergi, 2),
                "komisyon_tl": round(komisyon, 2),
                "fon_yonetim_gideri_tl": round(fon_gideri, 2),
                "toplam_kesinti_tl": round(toplam_kesinti, 2),
                "net_kar_tl": round(net_kar, 2)
            },
            "yapay_zeka_analizi": yapay_zeka_yorumu
        }

    except Exception as e:
        print(f"Maliyet Motoru Hatası: {e}")
        return {"durum": "hata", "mesaj": str(e)}
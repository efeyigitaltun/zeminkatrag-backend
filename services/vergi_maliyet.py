import os
import json
from services.ai_core import guvenli_llm_cagir, guvenli_json_parse

# JSON dosyasının yolunu bul ve oku
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VERGI_JSON_PATH = os.path.join(BASE_DIR, "vergi_kurallari.json")

def kurallari_yukle():
    """Dışarıdaki vergi_kurallari.json dosyasını okur. Bulamazsa acil durum değerlerini döner."""
    try:
        with open(VERGI_JSON_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Vergi Config Okuma Hatası: {e}")
        # Acil Durum (Fallback) Mevzuatı
        return {
            "hisse": {"komisyon_orani": 0.002, "stopaj_orani": 0.0}, 
            "fon": {"yillik_yonetim_gideri_orani": 0.025, "stopaj_orani": 0.10}, 
            "kripto": {"komisyon_orani": 0.002, "islem_vergisi_orani": 0.0, "gelir_vergisi_orani": 0.0},
            "yasal_uyari": "Sistem güncel vergi verilerine ulaşamadı, varsayılan oranlar kullanılıyor."
        }

def vergi_ve_maliyet_hesapla(varlik_tipi: str, alis_tutari: float, satis_tutari: float, elde_tutma_suresi_ay: int):
    """Güncel JSON config dosyasına göre maliyetleri hesaplar ve şeffaf kalemlere böler."""
    try:
        kurallar = kurallari_yukle()
        varlik = varlik_tipi.lower()
        
        brut_kar = satis_tutari - alis_tutari
        getiri_orani = (brut_kar / alis_tutari) * 100

        komisyon = 0.0
        vergi = 0.0
        fon_gideri = 0.0
        kesinti_kalemleri = []

        # 1. HİSSE SENEDİ MATEMATİĞİ
        if varlik == "hisse":
            komisyon = (alis_tutari + satis_tutari) * kurallar["hisse"]["komisyon_orani"]
            vergi = brut_kar * kurallar["hisse"]["stopaj_orani"] if brut_kar > 0 else 0
            
            kesinti_kalemleri.append({
                "isim": "Borsa / Aracı Kurum Komisyonu",
                "tutar": round(komisyon, 2),
                "oran_metni": f"%{kurallar['hisse']['komisyon_orani']*100} (Alış+Satış Toplamı)",
                "aciklama": "İşlemler sırasında aracı kurumun ve borsanın tahsil ettiği hizmet bedelidir."
            })
            kesinti_kalemleri.append({
                "isim": "Gelir Vergisi (Stopaj)",
                "tutar": round(vergi, 2),
                "oran_metni": f"%{kurallar['hisse']['stopaj_orani']*100}",
                "aciklama": "Elde ettiğiniz net kâr üzerinden kesilen yasal stopajdır. BIST hisselerinde şu an %0'dır."
            })

        # 2. YATIRIM FONU MATEMATİĞİ
        elif varlik == "fon":
            fon_gideri = alis_tutari * kurallar["fon"]["yillik_yonetim_gideri_orani"] * (elde_tutma_suresi_ay / 12)
            vergi = brut_kar * kurallar["fon"]["stopaj_orani"] if brut_kar > 0 else 0
            
            kesinti_kalemleri.append({
                "isim": "Fon Yönetim Gideri (MKK)",
                "tutar": round(fon_gideri, 2),
                "oran_metni": f"Yıllık %{kurallar['fon']['yillik_yonetim_gideri_orani']*100}",
                "aciklama": f"Fonun profesyonel yönetimi için içeride kaldığınız {elde_tutma_suresi_ay} aya oranlanarak fiyattan düşülen ücrettir."
            })
            kesinti_kalemleri.append({
                "isim": "Gelir Vergisi (Stopaj)",
                "tutar": round(vergi, 2),
                "oran_metni": f"%{kurallar['fon']['stopaj_orani']*100}",
                "aciklama": "Kâr elde ederek fondan çıkış yaptığınızda devletin doğrudan kestiği vergidir."
            })

        # 3. KRİPTO VARLIK MATEMATİĞİ
        elif varlik == "kripto":
            komisyon = (alis_tutari + satis_tutari) * kurallar["kripto"]["komisyon_orani"]
            islem_vergisi = (alis_tutari + satis_tutari) * kurallar["kripto"]["islem_vergisi_orani"]
            gelir_vergisi = brut_kar * kurallar["kripto"]["gelir_vergisi_orani"] if brut_kar > 0 else 0
            vergi = islem_vergisi + gelir_vergisi

            kesinti_kalemleri.append({
                "isim": "Borsa Platform Komisyonu",
                "tutar": round(komisyon, 2),
                "oran_metni": f"%{kurallar['kripto']['komisyon_orani']*100} (Alış+Satış)",
                "aciklama": "Kripto borsasının işlemi gerçekleştirmek için kestiği Maker/Taker komisyonudur."
            })
            kesinti_kalemleri.append({
                "isim": "Yasal İşlem ve Gelir Vergisi",
                "tutar": round(vergi, 2),
                "oran_metni": f"İşlem: %{kurallar['kripto']['islem_vergisi_orani']*100} | Gelir: %{kurallar['kripto']['gelir_vergisi_orani']*100}",
                "aciklama": "SPK/MASAK yasaları kapsamında tahsil edilebilecek yasal vergilerdir."
            })

        # --- GENEL TOPLAMLAR ---
        toplam_kesinti = komisyon + vergi + fon_gideri
        net_kar = brut_kar - toplam_kesinti

        # --- YAPAY ZEKA YORUMU ---
        prompt = f"""Sen ZeminKatRAG'in Vergi ve Maliyet Optimizasyon uzmanısın.
        Kullanıcıya brüt kârın 'gizli maliyetlerle' nasıl eridiğini göster.

        [MATEMATİKSEL VERİLER]
        - Varlık Tipi: {varlik_tipi.upper()}
        - Brüt Kâr: {brut_kar:.2f} TL (%{getiri_orani:.2f})
        - Toplam Gizli Kesinti: {toplam_kesinti:.2f} TL
        - Eline Geçecek Net Kâr: {net_kar:.2f} TL

        Lütfen SADECE aşağıdaki yapıda geçerli JSON dön:
        {{
            "gizli_maliyet_analizi": "Brüt kar ile net kar arasındaki farkı anlatan acımasız ama gerçekçi bir yorum.",
            "optimizasyon_tavsiyesi": "Bu maliyetleri (varsa komisyon veya vergiyi) düşürmek için yapılabilecek akıllıca bir tavsiye."
        }}
        """

        cevap = guvenli_llm_cagir(prompt)
        yapay_zeka_yorumu = guvenli_json_parse(cevap.text)

        if yapay_zeka_yorumu.get("durum") == "hata":
            return yapay_zeka_yorumu

        # --- FİNAL JSON ÇIKTISI (Frontend İçin Harika Bir Obje) ---
        return {
            "durum": "başarılı",
            "finansal_tablo": {
                "brut_kar_tl": round(brut_kar, 2),
                "toplam_kesinti_tl": round(toplam_kesinti, 2),
                "net_kar_tl": round(net_kar, 2),
                "kesinti_kalemleri": kesinti_kalemleri # Osman burayı Liste (ListView) olarak ekrana basacak
            },
            "yapay_zeka_analizi": yapay_zeka_yorumu,
            "yasal_uyari": kurallar["yasal_uyari"]
        }

    except Exception as e:
        return {"durum": "hata", "mesaj": f"Maliyet hesaplama hatası: {str(e)}"}
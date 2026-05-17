import os
import json
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv

load_dotenv()

# DÜZELTME BURADA YAPILDI: llm yerine llm_ana
llm_ana = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash", 
    google_api_key=os.environ.get("GEMINI_API_KEY")
)

llm_yedek = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash", 
    google_api_key=os.environ.get("GEMINI_API_KEY_BACKUP")
)

def portfoy_saglik_skoru_hesapla(varliklar: list, risk_profili: str):
    """
    Kullanıcının portföyünü alır, çeşitlendirme, risk uyumu ve korelasyon 
    açısından analiz edip 100 üzerinden skorlar.
    varliklar: [{"sembol": "BTC", "tutar": 10000}, {"sembol": "AAPL", "tutar": 5000}...]
    """
    try:
        toplam_deger = sum(item["tutar"] for item in varliklar)
        if toplam_deger == 0:
            return {"durum": "hata", "mesaj": "Portföy büyüklüğü sıfır olamaz."}

        # Portföy dağılımını yüzdelik olarak hazırla (LLM'in işini kolaylaştıralım)
        dagilim_metni = ""
        for item in varliklar:
            yuzde = (item["tutar"] / toplam_deger) * 100
            dagilim_metni += f"- {item['sembol']}: %{yuzde:.2f} ({item['tutar']} TL)\n"

        prompt = f"""Sen ZeminKatRAG'in Portföy Analiz Motorusun.
        Kullanıcının portföyünü şu 3 kritere göre acımasız ama yapıcı bir şekilde analiz et:
        1. Çeşitlendirme (Tek bir varlık sınıfına yığılma var mı?)
        2. Korelasyon (Aynı yönde hareket eden, örneğin hepsi teknoloji hissesi olan varlıklar riski artırır)
        3. Risk-Getiri Uyumu (Kullanıcının beyan ettiği risk profili: {risk_profili.upper()})

        [KULLANICI PORTFÖYÜ]
        Toplam Büyüklük: {toplam_deger} TL
        Dağılım:
        {dagilim_metni}

        Lütfen SADECE aşağıdaki yapıda geçerli bir JSON formatında cevap ver (başka metin ekleme):
        {{
            "genel_skor": 100 üzerinden bir tamsayı (örn: 75),
            "cesitlendirme_yorumu": "Çeşitlendirme durumu hakkında kısa yorum",
            "korelasyon_uyarisi": "Eğer varsa tehlikeli korelasyon uyarısı, yoksa 'Güvenli'",
            "risk_uyumu": "Profil ile portföy örtüşüyor mu?",
            "aksiyon_onerisi": "Dengelemek için satılması veya alınması mantıklı olabilecek varlık sınıfı önerisi"
        }}
        """

        try:
            cevap = llm_ana.invoke(prompt)
        except Exception as e:
            hata_mesaji = str(e)
            if "429" in hata_mesaji or "RESOURCE_EXHAUSTED" in hata_mesaji:
                print("⚠️ [DİKKAT] Ana API Limiti Doldu! Yedek Motora Geçiliyor...")
                cevap = llm_yedek.invoke(prompt)
            else:
                raise e # Limit dışı başka bir hataysa normal şekilde fırlat
        
        # Gemini'dan gelen JSON metnini temizleyip Python sözlüğüne çeviriyoruz
        temiz_json = cevap.content.replace("```json", "").replace("```", "").strip()
        analiz_sonucu = json.loads(temiz_json)
        
        return {"durum": "başarılı", "analiz": analiz_sonucu}

    except Exception as e:
        print(f"Portföy Analiz Hatası: {e}")
        return {"durum": "hata", "mesaj": str(e)}
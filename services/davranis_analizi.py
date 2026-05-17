import os
import json
import yfinance as yf
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv

load_dotenv()

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash", 
    google_api_key=os.environ.get("GEMINI_API_KEY")
)

def otomatik_piyasa_durumu_bul(sembol: str):
    """
    yfinance kullanarak varlığın son 1 aylık trendini hesaplar ve 
    piyasanın psikolojik durumunu (Boğa/Ayı/Yatay) tespit eder.
    """
    try:
        varlik = yf.Ticker(sembol)
        hist = varlik.history(period="1mo")
        
        if hist.empty:
            return "Veri Yok"
            
        ilk_fiyat = hist['Close'].iloc[0]
        son_fiyat = hist['Close'].iloc[-1]
        degisim = ((son_fiyat - ilk_fiyat) / ilk_fiyat) * 100
        
        if degisim > 15:
            return "Güçlü Yükseliş Rallisi (FOMO / Aşırı Alım Bölgesi)"
        elif degisim > 5:
            return "Pozitif Trend (Ilımlı Yükseliş)"
        elif degisim < -15:
            return "Sert Düşüş / Çöküş (Korku ve Panik Bölgesi)"
        elif degisim < -5:
            return "Negatif Trend (Ilımlı Düşüş)"
        else:
            return "Yatay ve Belirsiz Piyasa"
    except Exception:
        return "Bilinmiyor"

def davranisal_bias_tespit_et(islem_gecmisi: list):
    """
    Kullanıcının işlemlerini otomatik piyasa verileriyle harmanlar.
    islem_gecmisi: [{"sembol": "BTC-USD", "islem": "SAT", "kar_zarar": "%-25"}, ...]
    """
    try:
        if not islem_gecmisi or len(islem_gecmisi) < 3:
            return {"durum": "bilgi", "mesaj": "Analiz için en az 3 işlem gerekli."}

        gecmis_metni = ""
        for i, islem in enumerate(islem_gecmisi, 1):
            sembol = islem['sembol']
            # KULLANICIYA SORMUYORUZ, SİSTEM KENDİSİ BULUYOR!
            piyasa_durumu = otomatik_piyasa_durumu_bul(sembol) 
            
            gecmis_metni += f"{i}. İşlem: {sembol} -> {islem['islem']} | Sonuç: {islem['kar_zarar']} | Arka Plan Piyasa Analizi: {piyasa_durumu}\n"

        prompt = f"""Sen Davranışsal Finans ve Psikoloji uzmanısın.
        Kullanıcının aşağıdaki işlemlerini ve sistemin otomatik çektiği piyasa durumlarını inceleyerek Bilişsel Önyargıları (Cognitive Biases) tespit et.
        
        [KULLANICININ İŞLEM GEÇMİŞİ VE PİYASA GERÇEKLERİ]
        {gecmis_metni}

        Lütfen SADECE aşağıdaki yapıda geçerli bir JSON formatında cevap ver:
        {{
            "tespit_edilen_zaaf": "En belirgin psikolojik hata (Örn: Panik Satışı)",
            "analiz_ozeti": "Kullanıcının bu işlemlerdeki psikolojisini açıklayan özet.",
            "kocun_tavsiyesi": "Bu psikolojiyi yenmek için yatırım tavsiyesi."
        }}
        """

        cevap = llm.invoke(prompt)
        temiz_json = cevap.content.replace("```json", "").replace("```", "").strip()
        return {"durum": "başarılı", "davranis_analizi": json.loads(temiz_json)}

    except Exception as e:
        return {"durum": "hata", "mesaj": str(e)}
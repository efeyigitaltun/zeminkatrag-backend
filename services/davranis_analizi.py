import yfinance as yf
from services.ai_core import guvenli_llm_cagir, guvenli_json_parse

def dinamik_sembol_cozucu(sembol: str):
    """Kullanıcının girdiği sembolün gerçek piyasa karşılığını tahmin eder."""
    sembol = sembol.upper().strip()
    if sembol.endswith(".IS") or "-USD" in sembol:
        return sembol
        
    bilinen_kriptolar = ["BTC", "ETH", "USDT", "BNB", "SOL", "XRP", "ADA", "AVAX", "DOGE", "DOT"]
    if sembol in bilinen_kriptolar:
        return f"{sembol}-USD"
    return f"{sembol}.IS"

def davranisal_bias_tespit_et(islem_gecmisi: list):
    """Kullanıcının güncel işlemlerini, TOPLU ve hızlı çekilen piyasa verileriyle harmanlar."""
    try:
        if not islem_gecmisi or len(islem_gecmisi) < 3:
            return {"durum": "bilgi", "mesaj": "Analiz için en az 3 işlem gerekli."}

        # 1. ADIM: Tüm sembolleri önce çöz ve tek bir listede topla
        cozulmus_semboller = [dinamik_sembol_cozucu(islem['sembol']) for islem in islem_gecmisi]
        
        # 2. ADIM: TOPLU SORGULAMA (İnternete 3 kez değil, TEK BİR KEZ çıkıyoruz)
        # Örn: yf.download("THYAO.IS BTC-USD AAPL", period="1mo", group_by="ticker")
        sorgu_metni = " ".join(cozulmus_semboller)
        toplu_veri = yf.download(sorgu_metni, period="1mo", progress=False)

        gecmis_metni = ""
        
        # 3. ADIM: İndirilen toplu veriyi hafızadan hızlıca oku
        for i, islem in enumerate(islem_gecmisi):
            orijinal_sembol = islem['sembol']
            dogru_sembol = cozulmus_semboller[i]
            islem_tipi = islem['islem']
            kar_zarar = islem['kar_zarar']
            
            piyasa_durumu = "Belirsiz Piyasa"
            
            try:
                # Toplu veriden ilgili hissenin kapanış fiyatlarını çekiyoruz
                if len(cozulmus_semboller) == 1:
                    hist = toplu_veri['Close']
                else:
                    hist = toplu_veri[dogru_sembol]['Close']
                
                hist = hist.dropna()
                if not hist.empty:
                    ilk_fiyat = hist.iloc[0]
                    son_fiyat = hist.iloc[-1]
                    degisim = ((son_fiyat - ilk_fiyat) / ilk_fiyat) * 100
                    
                    if degisim > 15:
                        piyasa_durumu = "Güçlü Yükseliş Rallisi (FOMO / Aşırı Alım Bölgesi)"
                    elif degisim > 5:
                        piyasa_durumu = "Pozitif Trend (Ilımlı Yükseliş)"
                    elif degisim < -15:
                        piyasa_durumu = "Sert Düşüş / Çöküş (Korku ve Panik Bölgesi)"
                    elif degisim < -5:
                        piyasa_durumu = "Negatif Trend (Ilımlı Düşüş)"
                    else:
                        piyasa_durumu = "Yatay ve Belirsiz Piyasa"
            except Exception:
                piyasa_durumu = "Veri Alınamadı"

            gecmis_metni += f"{i+1}. İşlem: {orijinal_sembol} -> {islem_tipi} | Sonuç: {kar_zarar} | O Anki Piyasa Durumu: {piyasa_durumu}\n"

        # 4. ADIM: Yapay Zekaya Gönder
        prompt = f"""Sen Davranışsal Finans ve Psikoloji uzmanısın.
        Kullanıcının yakın zamanda yaptığı aşağıdaki işlemleri ve sistemin otomatik çektiği güncel piyasa durumlarını inceleyerek Bilişsel Önyargıları (Cognitive Biases) tespit et.
        
        [KULLANICININ GÜNCEL İŞLEM GEÇMİŞİ VE PİYASA GERÇEKLERİ]
        {gecmis_metni}

        Lütfen SADECE aşağıdaki yapıda geçerli bir JSON formatında cevap ver:
        {{
            "tespit_edilen_zaaf": "En belirgin psikolojik hata",
            "analiz_ozeti": "Kullanıcının bu işlemlerdeki psikolojisini açıklayan özet.",
            "kocun_tavsiyesi": "Bu psikolojiyi yenmek için yatırım tavsiyesi."
        }}
        """

        cevap = guvenli_llm_cagir(prompt)
        analiz_sonucu = guvenli_json_parse(cevap)

        if analiz_sonucu.get("durum") == "hata":
            return analiz_sonucu

        return {"durum": "başarılı", "davranis_analizi": analiz_sonucu}

    except Exception as e:
        return {"durum": "hata", "mesaj": str(e)}
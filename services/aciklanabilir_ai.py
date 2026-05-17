import os
import json
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv

load_dotenv()

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash", 
    google_api_key=os.environ.get("GEMINI_API_KEY")
)

def oneriyi_acikla(onerilen_islem: str, risk_profili: str, hedef_sure_ay: int, piyasa_ozeti: str):
    """
    Yapay zekanın verdiği bir önerinin arkasındaki 4 ana kriteri açıklar.
    """
    try:
        prompt = f"""Sen ZeminKatRAG'in Şeffaf Yapay Zeka (XAI) motorusun. 
        Bir yatırım önerisi verildi ve kullanıcı 'Neden?' diye soruyor. 
        Şu verilere dayanarak önerinin mantıksal dayanaklarını açıkla:

        [VERİLER]
        - Önerilen İşlem/Varlık: {onerilen_islem}
        - Kullanıcı Risk Profili: {risk_profili.upper()}
        - Hedef Süre (Vade): {hedef_sure_ay} Ay
        - Mevcut Piyasa Özeti: {piyasa_ozeti}

        Lütfen SADECE aşağıdaki yapıda geçerli bir JSON formatında cevap ver:
        {{
            "risk_uyumu_analizi": "Önerinin kullanıcının risk profiline (düşük/orta/yüksek) nasıl hizmet ettiği.",
            "vade_analizi": "Vade süresinin (kısa/uzun) bu varlık için neden uygun olduğu.",
            "piyasa_dayanagi": "Haber akışı ve piyasa trendlerinin bu öneriyi nasıl desteklediği.",
            "guven_skoru": "100 üzerinden bu öneriye duyulan güven derecesi"
        }}
        """

        cevap = llm.invoke(prompt)
        temiz_json = cevap.content.replace("```json", "").replace("```", "").strip()
        
        return {"durum": "başarılı", "aciklama": json.loads(temiz_json)}

    except Exception as e:
        return {"durum": "hata", "mesaj": str(e)}
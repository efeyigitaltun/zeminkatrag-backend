import os
import urllib.request
import xml.etree.ElementTree as ET
from supabase import create_client, Client
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI


load_dotenv()

# 1. Supabase Bağlantısı
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

# 2. Gemini Embedding Modeli 
# 2. Gemini Embedding Modeli (YENİ NESİL MODELE GÜNCELLENDİ)
embeddings = GoogleGenerativeAIEmbeddings(
    model="models/gemini-embedding-001", 
    google_api_key=os.environ.get("GEMINI_API_KEY")
)

def finansal_haberleri_vektorle(sembol: str):
    """
    Belirtilen hisse/kripto için %100 garantili RSS üzerinden haber çeker, 
    Gemini ile vektörleştirir ve Supabase'e yazar.
    """
    try:
        # RSS Linki (Yahoo Finance Garantili Akış)
        rss_url = f"https://feeds.finance.yahoo.com/rss/2.0/headline?s={sembol}"
        
        # Bot olmadığımızı kanıtlamak için tarayıcı kimliği (User-Agent) ekliyoruz
        req = urllib.request.Request(rss_url, headers={'User-Agent': 'Mozilla/5.0'})
        
        with urllib.request.urlopen(req) as response:
            xml_data = response.read()
            
        # Gelen XML verisini parçala
        root = ET.fromstring(xml_data)
        haberler = root.findall('.//item')
        
        eklenen_haber_sayisi = 0
        
        for haber in haberler:
            baslik = haber.find('title').text
            link = haber.find('link').text
            
            if not baslik:
                continue
                
            # 3. Metni Vektöre Çevir (Gemini Çalışıyor)
            vektor = embeddings.embed_query(baslik)
            
            # 4. Supabase'e Kaydet
            veri = {
                "haber_metni": baslik,
                "kaynak": link,
                "embedding": vektor
            }
            
            supabase.table("haber_vektorleri").insert(veri).execute()
            eklenen_haber_sayisi += 1
            
        return {"durum": "başarılı", "mesaj": f"{sembol} için {eklenen_haber_sayisi} haber RSS üzerinden hafızaya eklendi."}
        
    except Exception as e:
        print(f"RAG Hatası: {e}")
        return {"durum": "hata", "mesaj": str(e)}
    # 5. Gemini'ın Metin Üreten (Chat) Modeli
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash", 
    google_api_key=os.environ.get("GEMINI_API_KEY")
)

def yapay_zeka_kocuna_sor(soru: str, risk_profili: str = "orta"):
    """
    Kullanıcının sorusunu risk profiliyle harmanlar, hafızadaki haberlerle 
    eşleştirir ve analojiler kullanarak profesyonelce cevaplar.
    """
    try:
        # 1. Soruyu vektöre çevir ve en benzer haberleri getir
        soru_vektoru = embeddings.embed_query(soru)
        response = supabase.rpc(
            "match_haberler",
            {
                "query_embedding": soru_vektoru,
                "match_threshold": 0.25, # Daha esnek arama için eşiği biraz düşürdük
                "match_count": 5
            }
        ).execute()
        
        benzer_haberler = response.data
        if benzer_haberler:
            baglam = "\n".join([f"- {h['haber_metni']}" for h in benzer_haberler])
        else:
            baglam = "Sistemde bu varlıkla ilgili doğrudan çok taze bir haber akışı yok."
            
        # 2. Gelişmiş Prompt Tasarımı (Kafandaki tüm kuralları buraya işledik)
        prompt = f"""Sen ZeminKatRAG uygulamasının üst düzey finansal yapay zeka koçusun. 
        Amacın, finansal okuryazarlığı artırmak ve kullanıcılara rehberlik etmektir.

        [KURALLAR]
        1. Yeni başlayan yatırımcıları ürkütmemek için karmaşık finansal terimleri (enflasyon, kaldıraç, likidite, RAG vb.) mutlaka günlük hayattan basit analojilerle (benzetmelerle) açıkla.
        2. Kullanıcının mevcut risk profili: **{risk_profili.upper()}**. Cevaplarını bu profile göre şekillendir. Eğer risk profili 'yüksek' ise inovatif varlıklara (kripto, teknoloji hisseleri) değinebilirsin; 'düşük' ise korumacı varlıklara (altın, devlet tahvili, likidite fonları) yönlendir.
        3. Doğrudan 'al/sat' sinyali verme. Analiz sun ama cümlenin sonuna mutlaka profesyonel ve yasal bir sorumluluk reddi (Yatırım tavsiyesi değildir) ibaresi ekle.

        [GÜNCEL PİYASA BİLGİLERİ]
        {baglam}

        [KULLANICININ SORUSU]
        {soru}
        """
        
        # 3. Gemini'ı çalıştır
        cevap = llm.invoke(prompt)
        kullanilan_kaynaklar = [h['haber_metni'] for h in benzer_haberler]
        
        return {
            "durum": "başarılı", 
            "cevap": cevap.content, 
            "kullanilan_haber_sayisi": len(benzer_haberler),
            "referans_haberler": kullanilan_kaynaklar
        }
        
    except Exception as e:
        print(f"Chat Hatası: {e}")
        return {"durum": "hata", "mesaj": str(e)}
    
def yerel_piyasa_ve_halka_arz_ogret():
    """
    Türkiye piyasasındaki halka arz, fon ve genel finans gündemini 
    Bloomberg HT RSS üzerinden çeker ve Gemini ile vektörleştirip Supabase'e yazar.
    """
    try:
        # Türkiye finans gündemi için güvenilir RSS kaynağı
        url_yerel = "https://www.bloomberght.com/rss" 
        
        req = urllib.request.Request(url_yerel, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            xml_data = response.read()
            
        root = ET.fromstring(xml_data)
        haberler = root.findall('.//item')
        
        eklenen = 0
        for haber in haberler:
            baslik = haber.find('title').text
            link = haber.find('link').text
            
            if not baslik:
                continue
                
            # Başlığı Gemini ile 3072 boyutlu vektöre çeviriyoruz
            vektor = embeddings.embed_query(baslik)
            
            veri = {
                "haber_metni": f"[Türkiye Piyasası Gündemi] {baslik}",
                "kaynak": link,
                "embedding": vektor
            }
            
            supabase.table("haber_vektorleri").insert(veri).execute()
            eklenen += 1
            
        return {"durum": "başarılı", "mesaj": f"Türkiye piyasasından {eklenen} güncel fon ve halka arz haberi hafızaya eklendi."}
    except Exception as e:
        return {"durum": "hata", "mesaj": str(e)}
    

    
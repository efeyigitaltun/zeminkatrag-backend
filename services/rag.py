import os
from dotenv import load_dotenv
from supabase import create_client, Client
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings

load_dotenv()

# --- GLOBAL TANIMLAMALAR (SCOPE DÜZELTMESİ - MADDE #3) ---
supabase_url = os.environ.get("SUPABASE_URL")
supabase_key = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(supabase_url, supabase_key)

aktif_anahtar = os.environ.get("GEMINI_API_KEY_ANA")
print(f"🔍 [RAG TEST] Vektörleme için kullanılan anahtarın son 4 hanesi: {aktif_anahtar[-4:]}")

embeddings = GoogleGenerativeAIEmbeddings(
    model="models/gemini-embedding-001", 
    google_api_key=os.environ.get("GEMINI_API_KEY_ANA")
)
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    google_api_key=os.environ.get("GEMINI_API_KEY_ANA"),
    temperature=0.3
)
# --------------------------------------------------------

def finansal_haberleri_vektorle(haber_listesi):
    """
    Haberleri alır, vektöre çevirir ve Supabase'e kaydeder.
    Dışarıdan gelen verinin Sözlük (dict) veya düz Metin (str) olmasına karşı korumalıdır.
    """
    try:
        if not haber_listesi:
            return {"durum": "bilgi", "mesaj": "İşlenecek haber bulunamadı."}

        # Eğer dışarıdan liste yerine yanlışlıkla tek bir düz metin gönderildiyse onu listeye çevir (Hata Önleyici)
        if isinstance(haber_listesi, str):
            haber_listesi = [haber_listesi]

        islenen_haber_sayisi = 0

        for haber in haber_listesi:
            # 1. Gelen verinin tipini kontrol et ve güvenli ayrıştırma yap
            if isinstance(haber, dict):
                # Veri senin yerel_piyasa fonksiyonundaki gibi düzgün bir formattaysa:
                metin = haber.get("metin", "")
                kaynak = haber.get("kaynak", "Bilinmeyen Kaynak")
            elif isinstance(haber, str):
                # Veri Swagger'daki THYAO sorgusundan gelen düz metinse:
                metin = haber
                # Supabase upsert işleminde aynı kaynak üstüne yazmasın diye kaynağı metinden üretiyoruz
                kaynak = f"Otomatik Çekim - {metin[:20]}..." 
            else:
                continue  # Bilinmeyen bir format gelirse çökme, diğer habere geç

            # Eğer haberin içi boşsa vektörlemeye çalışma
            if not metin or metin.strip() == "":
                continue

            # 2. Metni vektöre çevir
            vektor = embeddings.embed_query(metin)
            
            veri = {
                "kaynak": kaynak,
                "metin": metin,
                "vektor": vektor
            }
            
            # 3. Supabase'e kaydet (Aynı kaynak varsa üstüne yazar)
            supabase.table("haber_vektorleri").upsert(veri, on_conflict="kaynak").execute()
            islenen_haber_sayisi += 1
            
        return {"durum": "başarılı", "mesaj": f"{islenen_haber_sayisi} haber başarıyla işlendi ve Supabase'e aktarıldı."}

    except Exception as e:
        print(f"Vektörleme Hatası: {e}")
        return {"durum": "hata", "mesaj": str(e)}

def yapay_zeka_kocuna_sor(kullanici_mesaji: str, risk_profili: str):
    """
    Kullanıcının sorusunu RAG mantığıyla (haberlerle birleştirerek) cevaplar.
    """
    try:
        # 1. Soruyu vektöre çevir
        soru_vektoru = embeddings.embed_query(kullanici_mesaji)
        
        # 2. Supabase'den en benzer 3 haberi getir (match_haberler fonksiyonu)
        benzer_haberler = supabase.rpc(
            'match_haberler',
            {'query_embedding': soru_vektoru, 'match_threshold': 0.7, 'match_count': 3}
        ).execute()
        
        # 3. Gelen haberleri tek bir bağlam (context) metninde birleştir
        baglam = ""
        if benzer_haberler.data:
            for h in benzer_haberler.data:
                baglam += f"- {h['metin']} (Kaynak: {h['kaynak']})\n"

        # 4. LLM'e gönderilecek asıl prompt'u oluştur
        prompt = f"""Sen ZeminKatRAG'in baş finansal yapay zeka asistanısın.
        Kullanıcı Risk Profili: {risk_profili.upper()}
        
        [GÜNCEL PİYASA BİLGİLERİ (RAG)]
        {baglam if baglam else "Güncel haber bulunamadı."}
        
        [KULLANICI SORUSU]
        {kullanici_mesaji}
        
        Yukarıdaki piyasa bilgilerini kullanarak ve kullanıcının risk profilini dikkate alarak 
        objektif, profesyonel ve yönlendirici bir cevap ver.
        """
        
        # 5. Cevabı üret ve dön
        cevap = llm.invoke(prompt)
        return {"durum": "başarılı", "cevap": cevap.content}
        
    except Exception as e:
        print(f"RAG Hatası: {e}")
        return {"durum": "hata", "mesaj": str(e)}
    
def yerel_piyasa_ve_halka_arz_ogret():
    """
    Sisteme güncel Türkiye piyasası ve halka arz verilerini ekler.
    (Eğer önceden burada özel bir veri çekme kodun varsa buraya ekleyebilirsin)
    """
    try:
        # Sunucunun çökmemesi ve RAG hafızasının çalışması için temel şablon:
        yerel_haberler = [
            {"metin": "Borsa İstanbul BIST100 endeksinde güncel volatilite devam ediyor.", "kaynak": "bist-genel-bilgi"},
            {"metin": "SPK, yeni haftada 2 şirketin halka arzına (IPO) onay verdi.", "kaynak": "spk-halka-arz-bulteni"}
        ]
        
        # Elimizdeki verileri vektörleyip Supabase'e (hafızaya) yazıyoruz
        sonuc = finansal_haberleri_vektorle(yerel_haberler)
        return {"durum": "başarılı", "mesaj": "Yerel piyasa verileri RAG hafızasına eklendi.", "detay": sonuc}
        
    except Exception as e:
        print(f"Halka Arz Öğretme Hatası: {e}")
        return {"durum": "hata", "mesaj": str(e)}    
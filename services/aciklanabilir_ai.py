from services.ai_core import guvenli_llm_cagir, guvenli_json_parse

def oneriyi_acikla(onerilen_islem: str, risk_profili: str, hedef_sure_ay: int, piyasa_ozeti: str):
    """Yapay zekanın verdiği bir önerinin arkasındaki 4 ana kriteri açıklar."""
    try:
        prompt = f"""Sen ZeminKatRAG'in Şeffaf Yapay Zeka (XAI) motorusun. 
        Şu verilere dayanarak önerinin mantıksal dayanaklarını açıkla:

        [VERİLER]
        - Önerilen İşlem/Varlık: {onerilen_islem}
        - Kullanıcı Risk Profili: {risk_profili.upper()}
        - Hedef Süre (Vade): {hedef_sure_ay} Ay
        - Mevcut Piyasa Özeti: {piyasa_ozeti}

        Lütfen SADECE aşağıdaki yapıda geçerli bir JSON formatında cevap ver:
        {{
            "risk_uyumu_analizi": "Önerinin kullanıcının risk profiline nasıl hizmet ettiği.",
            "vade_analizi": "Vade süresinin bu varlık için neden uygun olduğu.",
            "piyasa_dayanagi": "Piyasa trendlerinin bu öneriyi nasıl desteklediği.",
            "guven_skoru": 95
        }}
        """

        # Çekirdek motor çağrısı ve merkezi parse işlemi
        cevap = guvenli_llm_cagir(prompt)
        aciklama_sonucu = guvenli_json_parse(cevap.text)

        if aciklama_sonucu.get("durum") == "hata":
            return aciklama_sonucu

        return {"durum": "başarılı", "aciklama": aciklama_sonucu}

    except Exception as e:
        return {"durum": "hata", "mesaj": str(e)}
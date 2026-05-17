import yfinance as yf

def get_live_price(sembol: str):
    """
    Verilen sembolün canlı fiyatını yfinance üzerinden çeker.
    Örnek semboller: 'AAPL', 'BTC-USD', 'THYAO.IS'
    """
    try:
        # Ticker objesini oluştur
        varlik = yf.Ticker(sembol)
        
        # fast_info, veriyi çekmenin en hızlı ve hafif yoludur
        fiyat = varlik.fast_info['lastPrice']
        
        # Fiyatı virgülden sonra 2 basamak olacak şekilde yuvarla
        return round(fiyat, 2)
    except Exception as e:
        print(f"Hata oluştu ({sembol}): {e}")
        return None
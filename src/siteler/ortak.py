"""Tüm site adaptörlerinin ortak Playwright ve metin ayrıştırma araçları."""

import re

from playwright.sync_api import sync_playwright

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")

# "12.400 TL", "₺12.400", "12.400,50 TL" gibi biçimleri yakalar
FIYAT_DESENI = re.compile(
    r"(?:₺|TL)\s*(\d{1,3}(?:\.\d{3})*(?:,\d{2})?)"
    r"|(\d{1,3}(?:\.\d{3})*(?:,\d{2})?)\s*(?:₺|TL)"
)

INDIRIM_ANAHTARLARI = ("indirim", "kampanya", "fırsat", "erken rezervasyon", "son dakika")


def sayfa_metni_al(url: str, bekle_saniye: int = 8) -> str:
    """Sayfayı headless Chromium ile açıp gövde metnini döndürür."""
    with sync_playwright() as p:
        tarayici = p.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled"],
        )
        baglam = tarayici.new_context(
            user_agent=UA,
            locale="tr-TR",
            timezone_id="Europe/Istanbul",
            viewport={"width": 1366, "height": 768},
        )
        sayfa = baglam.new_page()
        sayfa.goto(url, wait_until="domcontentloaded", timeout=60_000)
        sayfa.wait_for_timeout(bekle_saniye * 1000)  # dinamik fiyatların yüklenmesini bekle
        metin = sayfa.inner_text("body")
        tarayici.close()
    return metin


def sayiya_cevir(metin: str) -> float:
    """'12.400,50' gibi Türkçe biçimli tutarı sayıya çevirir."""
    return float(metin.replace(".", "").replace(",", "."))


def fiyatlari_bul(metin: str, taban: float = 500, tavan: float = 2_000_000) -> list[float]:
    """Metindeki tüm TL fiyatlarını döndürür; makul aralık dışını eler.

    Taban filtresi, "%15 TL indirim" gibi küçük tutarların ve kur/puan
    değerlerinin oda fiyatı sanılmasını önler.
    """
    fiyatlar = []
    for eslesme in FIYAT_DESENI.finditer(metin):
        ham = eslesme.group(1) or eslesme.group(2)
        try:
            deger = sayiya_cevir(ham)
        except ValueError:
            continue
        if taban <= deger <= tavan:
            fiyatlar.append(deger)
    return fiyatlar


def indirimleri_bul(metin: str) -> list[str]:
    """Kampanya/indirim içeren kısa satırları toplar (rozet ve banner metinleri)."""
    bulunanlar: list[str] = []
    for satir in metin.splitlines():
        satir = " ".join(satir.split())
        if not (5 <= len(satir) <= 80):
            continue
        if not satir[0].isalnum() and satir[0] != "%":
            continue  # "’a özel..." gibi kırpık/artık satırları ele
        kucuk = satir.lower()
        if any(a in kucuk for a in INDIRIM_ANAHTARLARI) and ("%" in satir or "TL" in satir or "indirim" in kucuk):
            if satir not in bulunanlar:
                bulunanlar.append(satir)
    return bulunanlar[:5]


def genel_fiyat_cek(url: str, bekle_saniye: int = 8) -> dict:
    """Varsayılan adaptör davranışı: sayfadaki en düşük makul TL fiyatını alır."""
    try:
        metin = sayfa_metni_al(url, bekle_saniye)
    except Exception as hata:  # zaman aşımı, ağ hatası vb.
        return {"fiyat": None, "indirimler": [], "hata": f"Sayfa açılamadı: {hata}"}

    fiyatlar = fiyatlari_bul(metin)
    if not fiyatlar:
        return {"fiyat": None, "indirimler": [],
                "hata": "Sayfada fiyat bulunamadı (bot koruması veya tasarım değişikliği olabilir)"}
    return {"fiyat": min(fiyatlar), "indirimler": indirimleri_bul(metin), "hata": None}

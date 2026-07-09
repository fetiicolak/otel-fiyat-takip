"""Site geneli kampanya/kupon takibi (örn. Obilet'in YAZFIRSATI kodu).

Sitelerin kampanya sayfalarından otel/konaklama ile ilgili kampanya
başlıklarını ve varsa indirim kodlarını toplar. Otel sayfasındaki oda bazlı
indirimlerden farklı olarak bunlar tüm rezervasyonlarda geçerli kuponlardır.
"""

from .siteler import ortak

OTEL_ANAHTARLARI = ("otel", "konaklama", "tatil")
INDIRIM_ANAHTARLARI = ("indirim", "kupon", "fırsat", "%")


def _ilgili_mi(satir: str) -> bool:
    k = ortak.kucult(satir)
    if not (10 <= len(satir) <= 120):
        return False
    return any(a in k for a in OTEL_ANAHTARLARI) and any(a in k for a in INDIRIM_ANAHTARLARI)


def kampanyalari_cek(url: str) -> list[str]:
    """Kampanya sayfasındaki otel ile ilgili kampanyaları 'başlık (Kod: X)' olarak döndürür."""
    metin = ortak.sayfa_metni_al(url, bekle_saniye=6)
    satirlar = [" ".join(s.split()) for s in metin.splitlines() if s.strip()]

    kampanyalar: list[str] = []
    for i, satir in enumerate(satirlar):
        if not _ilgili_mi(satir):
            continue
        kayit = satir
        # Takip eden birkaç satırda "İndirim kodu: XYZ" ara
        for j in range(i + 1, min(i + 5, len(satirlar))):
            sonraki = satirlar[j]
            if ortak.kucult(sonraki).startswith("indirim kodu"):
                kod = sonraki.split(":", 1)[1].strip() if ":" in sonraki and sonraki.split(":", 1)[1].strip() else \
                      (satirlar[j + 1].strip() if j + 1 < len(satirlar) else "")
                if kod and len(kod) <= 30:
                    kayit += f" (Kod: {kod})"
                break
            if _ilgili_mi(sonraki):  # sonraki kampanya başladı, kod yokmuş
                break
        if kayit not in kampanyalar:
            kampanyalar.append(kayit)
    return kampanyalar[:10]


def hepsini_cek(kampanya_sayfalari: dict[str, str]) -> dict[str, list[str] | None]:
    """Her site için kampanya listesi; okunamayan site için None döner."""
    sonuc: dict[str, list[str] | None] = {}
    for site, url in kampanya_sayfalari.items():
        try:
            sonuc[site] = kampanyalari_cek(url)
        except Exception as hata:
            print(f"[kampanya] {site} okunamadı: {hata}")
            sonuc[site] = None
    return sonuc

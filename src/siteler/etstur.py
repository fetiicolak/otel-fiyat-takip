"""Etstur otel sayfası adaptörü.

URL biçimi: https://www.etstur.com/<Otel-Slug>?check_in=GG.AA.YYYY&check_out=GG.AA.YYYY&adult_1=2

Sayfa yapısı: başlıkta "<fiyat> TL / Odaları Gör" (indirimli en düşük oda
fiyatı), oda listesinde "N Gece / <liste fiyatı> TL / ... / <indirimli> TL"
blokları. "X TL indirim kuponu" satırlarındaki kupon tutarları oda fiyatı
DEĞİLDİR — bu yüzden genel en-düşük-fiyat yaklaşımı burada kullanılmaz.
"""

import re

from . import ortak

BASLIK_FIYAT = re.compile(r"([\d.,]+)\s*TL\s*\n\s*Odaları Gör")
GECE_FIYAT = re.compile(r"Gece\s*\n\s*([\d.,]+)\s*TL")


def fiyat_cek(url: str) -> dict:
    try:
        metin = ortak.sayfa_metni_al(url, bekle_saniye=8)
    except Exception as hata:
        return {"fiyat": None, "indirimler": [], "hata": f"Sayfa açılamadı: {hata}"}

    eslesme = BASLIK_FIYAT.search(metin)
    if eslesme:
        fiyat = ortak.sayiya_cevir(eslesme.group(1))
    else:
        # Başlık fiyatı yoksa oda bloklarındaki "N Gece / fiyat" değerlerinin en düşüğü
        gece_fiyatlari = [ortak.sayiya_cevir(e.group(1)) for e in GECE_FIYAT.finditer(metin)]
        if not gece_fiyatlari:
            return {"fiyat": None, "indirimler": [],
                    "hata": "Oda fiyatı bulunamadı (sayfa yapısı değişmiş veya müsaitlik yok olabilir)"}
        fiyat = min(gece_fiyatlari)

    return {"fiyat": fiyat, "indirimler": ortak.indirimleri_bul(metin), "hata": None}

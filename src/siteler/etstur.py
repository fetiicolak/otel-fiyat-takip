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
        return {"fiyat": None, "normal_fiyat": None, "indirimler": [],
                "hata": f"Sayfa açılamadı: {hata}"}

    # Oda bloklarındaki "N Gece / <fiyat> TL" değerleri liste (normal) fiyatlardır
    gece_fiyatlari = [ortak.sayiya_cevir(e.group(1)) for e in GECE_FIYAT.finditer(metin)]
    normal = min(gece_fiyatlari) if gece_fiyatlari else None

    eslesme = BASLIK_FIYAT.search(metin)
    if eslesme:
        fiyat = ortak.sayiya_cevir(eslesme.group(1))  # başlık fiyatı: indirimli en düşük
    elif normal is not None:
        fiyat, normal = normal, None
    else:
        return {"fiyat": None, "normal_fiyat": None, "indirimler": [],
                "hata": "Oda fiyatı bulunamadı (sayfa yapısı değişmiş veya müsaitlik yok olabilir)"}
    if normal is not None and normal <= fiyat:
        normal = None

    return {"fiyat": fiyat, "normal_fiyat": normal,
            "indirimler": ortak.indirimleri_bul(metin), "hata": None}

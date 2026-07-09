"""Obilet otel sayfası adaptörü.

Sayfa yapısı (gövde metni sırasıyla): gezinme → oda listesi → "Hakkında"
bölümü → "Benzer Oteller/Tesisler" karuseli (BAŞKA otellerin fiyatları!) →
sepete özel indirim banner'ı. Fiyat yalnızca oda listesinden alınmalı;
aksi hâlde komşu otel fiyatları ve indirim tutarları en düşük fiyat sanılır.

Her oda satırı "Odayı Seç" ile bittiği için oda listesi bölgesi, son
"Odayı Seç" ifadesine kadar olan kısımdır. ("Hakkında" kelimesi üst gezinme
sekmelerinde de geçtiğinden bölüm sınırı olarak kullanılamaz.)
"""

import re

from . import ortak

SEPET_BANNER = re.compile(r"sepete özel\s+([\d.,]+\s*TL)\s+[İi]ndirim", re.IGNORECASE)
SEPETE_OZEL_FIYAT = re.compile(r"Sepete Özel\s+([\d.,]+)\s*TL")


def _oda_bolumu(metin: str) -> str | None:
    son = metin.rfind("Odayı Seç")
    if son == -1:
        return None  # oda listesi yok: müsaitlik bitmiş veya sayfa değişmiş
    return metin[:son]


def fiyat_cek(url: str) -> dict:
    try:
        metin = ortak.sayfa_metni_al(url, bekle_saniye=8)
    except Exception as hata:
        return {"fiyat": None, "normal_fiyat": None, "indirimler": [],
                "hata": f"Sayfa açılamadı: {hata}"}

    oda_metni = _oda_bolumu(metin)
    if oda_metni is None:
        return {"fiyat": None, "normal_fiyat": None, "indirimler": [],
                "hata": "Oda listesi bulunamadı (müsaitlik yok veya sayfa yapısı değişmiş olabilir)"}
    fiyatlar = ortak.fiyatlari_bul(oda_metni)
    if not fiyatlar:
        return {"fiyat": None, "normal_fiyat": None, "indirimler": [],
                "hata": "Oda fiyatı bulunamadı (sayfa yapısı değişmiş olabilir)"}

    indirimler = ortak.indirimleri_bul(oda_metni)
    banner = SEPET_BANNER.search(metin)
    if banner:
        indirim = f"Sepete özel {banner.group(1)} indirim"
        if indirim not in indirimler:
            indirimler.append(indirim)

    # İndirimli fiyat = en ucuz odanın "Sepete Özel" fiyatı; normal fiyat = liste fiyatı
    sepete_ozel = {ortak.sayiya_cevir(e.group(1)) for e in SEPETE_OZEL_FIYAT.finditer(oda_metni)}
    sepete_ozel = {f for f in sepete_ozel if f >= 500}
    if sepete_ozel:
        fiyat = min(sepete_ozel)
        liste_fiyatlari = [f for f in fiyatlar if f not in sepete_ozel]
        normal = min(liste_fiyatlari) if liste_fiyatlari else None
    else:
        fiyat, normal = min(fiyatlar), None
    if normal is not None and normal <= fiyat:
        normal = None

    return {"fiyat": fiyat, "normal_fiyat": normal, "indirimler": indirimler, "hata": None}

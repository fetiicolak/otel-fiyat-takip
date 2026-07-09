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


def _oda_bolumu(metin: str) -> str | None:
    son = metin.rfind("Odayı Seç")
    if son == -1:
        return None  # oda listesi yok: müsaitlik bitmiş veya sayfa değişmiş
    return metin[:son]


def fiyat_cek(url: str) -> dict:
    try:
        metin = ortak.sayfa_metni_al(url, bekle_saniye=8)
    except Exception as hata:
        return {"fiyat": None, "indirimler": [], "hata": f"Sayfa açılamadı: {hata}"}

    oda_metni = _oda_bolumu(metin)
    if oda_metni is None:
        return {"fiyat": None, "indirimler": [],
                "hata": "Oda listesi bulunamadı (müsaitlik yok veya sayfa yapısı değişmiş olabilir)"}
    fiyatlar = ortak.fiyatlari_bul(oda_metni)
    if not fiyatlar:
        return {"fiyat": None, "indirimler": [],
                "hata": "Oda fiyatı bulunamadı (sayfa yapısı değişmiş olabilir)"}

    indirimler = ortak.indirimleri_bul(oda_metni)
    banner = SEPET_BANNER.search(metin)
    if banner:
        indirim = f"Sepete özel {banner.group(1)} indirim"
        if indirim not in indirimler:
            indirimler.append(indirim)

    # En düşük bölüm fiyatı = en ucuz odanın sepete özel fiyatı
    return {"fiyat": min(fiyatlar), "indirimler": indirimler, "hata": None}

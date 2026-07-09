"""Yeni fiyatı öncekiyle karşılaştırıp bildirilecek olayları üretir."""

SITE_ADLARI = {"obilet": "Obilet", "hotelscom": "Hotels.com", "etstur": "Etstur"}


def _tl(fiyat: float) -> str:
    return f"{fiyat:,.0f} TL".replace(",", ".")


def karsilastir(otel: dict, site: str, onceki: dict | None,
                onceki_herhangi: dict | None, yeni: dict, ayarlar: dict) -> list[str]:
    """Bildirilecek mesajların listesini döndürür (boş liste = bildirim yok).

    onceki          : son BAŞARILI kayıt (fiyat karşılaştırması için)
    onceki_herhangi : son kayıt, hatalı da olabilir (hata spam'ini önlemek için)
    """
    site_ad = SITE_ADLARI.get(site, site)
    baslik = f"<b>{otel['ad']} — {site_ad}</b>"
    detay = f"📅 {otel.get('giris', '?')} → {otel.get('cikis', '?')} · {otel.get('kisi', '')}"
    mesajlar: list[str] = []

    # Okuma hatası: yalnızca yeni oluşan hatada bildir (her 4 saatte bir tekrar etmesin)
    if yeni.get("hata"):
        onceden_de_hatali = onceki_herhangi is not None and onceki_herhangi.get("hata")
        if not onceden_de_hatali and onceki_herhangi is not None:
            mesajlar.append(f"⚠️ {baslik}\nSite okunamadı: {yeni['hata']}")
        return mesajlar

    fiyat = yeni["fiyat"]

    # İlk başarılı kayıt: takip başladı bilgisi
    if onceki is None:
        mesajlar.append(f"✅ {baslik}\nTakip başladı. Güncel en düşük fiyat: <b>{_tl(fiyat)}</b>\n{detay}")
        if yeni.get("indirimler"):
            mesajlar[-1] += "\n🏷️ Aktif kampanyalar: " + " | ".join(yeni["indirimler"])
        return mesajlar

    eski_fiyat = onceki["fiyat"]
    fark = fiyat - eski_fiyat
    yuzde = abs(fark) / eski_fiyat * 100 if eski_fiyat else 0
    esik_asildi = abs(fark) >= ayarlar.get("esik_tl", 250) or yuzde >= ayarlar.get("esik_yuzde", 3)

    if fark < 0 and esik_asildi:
        mesajlar.append(
            f"🔻 {baslik}\n{_tl(eski_fiyat)} → <b>{_tl(fiyat)}</b> (%{yuzde:.1f} düştü)\n{detay}\n{yeni['url']}"
        )
    elif fark > 0 and esik_asildi:
        mesajlar.append(
            f"🔺 {baslik}\n{_tl(eski_fiyat)} → <b>{_tl(fiyat)}</b> (%{yuzde:.1f} arttı)\n{detay}"
        )

    # Daha önce görülmeyen kampanya metinleri
    yeni_indirimler = set(yeni.get("indirimler", [])) - set(onceki.get("indirimler", []))
    if yeni_indirimler:
        mesajlar.append(
            f"🏷️ {baslik}\nYeni kampanya: " + " | ".join(sorted(yeni_indirimler)) +
            f"\nGüncel fiyat: <b>{_tl(fiyat)}</b>\n{yeni['url']}"
        )

    return mesajlar


def gunluk_ozet(oteller: list[dict], kayitlar: list[dict]) -> str:
    """Tüm otellerin güncel durumunu tek mesajda özetler."""
    from . import depo

    satirlar = ["📋 <b>Günlük Fiyat Özeti</b>"]
    for otel in oteller:
        satirlar.append(f"\n🏨 <b>{otel['ad']}</b> ({otel.get('giris', '?')} → {otel.get('cikis', '?')})")
        for kaynak in otel["kaynaklar"]:
            site_ad = SITE_ADLARI.get(kaynak["site"], kaynak["site"])
            son = depo.son_basarili(kayitlar, otel["id"], kaynak["site"])
            if son:
                satir = f"  • {site_ad}: <b>{_tl(son['fiyat'])}</b>"
                if son.get("indirimler"):
                    satir += " 🏷️ " + " | ".join(son["indirimler"][:2])
            else:
                satir = f"  • {site_ad}: veri yok ⚠️"
            satirlar.append(satir)
    return "\n".join(satirlar)

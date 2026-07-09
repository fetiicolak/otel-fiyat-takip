"""Yeni fiyatı öncekiyle karşılaştırıp bildirilecek olayları üretir."""

SITE_ADLARI = {"obilet": "Obilet", "hotelscom": "Hotels.com", "etstur": "Etstur"}


def _tl(fiyat: float) -> str:
    return f"{fiyat:,.0f} TL".replace(",", ".")


def _fiyat_metni(kayit: dict) -> str:
    """'<b>8.750 TL</b> (liste: 9.600 TL)' — normal fiyat varsa ikisini de gösterir."""
    metin = f"<b>{_tl(kayit['fiyat'])}</b>"
    if kayit.get("normal_fiyat"):
        metin += f" (liste: {_tl(kayit['normal_fiyat'])})"
    return metin


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
        mesajlar.append(f"✅ {baslik}\nTakip başladı. Güncel en düşük fiyat: {_fiyat_metni(yeni)}\n{detay}")
        if yeni.get("indirimler"):
            mesajlar[-1] += "\n🏷️ Aktif kampanyalar: " + " | ".join(yeni["indirimler"])
        return mesajlar

    eski_fiyat = onceki["fiyat"]
    fark = fiyat - eski_fiyat
    yuzde = abs(fark) / eski_fiyat * 100 if eski_fiyat else 0
    esik_asildi = abs(fark) >= ayarlar.get("esik_tl", 250) or yuzde >= ayarlar.get("esik_yuzde", 3)

    if fark < 0 and esik_asildi:
        mesajlar.append(
            f"🔻 {baslik}\n{_tl(eski_fiyat)} → {_fiyat_metni(yeni)} (%{yuzde:.1f} düştü)\n{detay}\n{yeni['url']}"
        )
    elif fark > 0 and esik_asildi:
        mesajlar.append(
            f"🔺 {baslik}\n{_tl(eski_fiyat)} → {_fiyat_metni(yeni)} (%{yuzde:.1f} arttı)\n{detay}"
        )

    # Daha önce görülmeyen kampanya metinleri
    yeni_indirimler = set(yeni.get("indirimler", [])) - set(onceki.get("indirimler", []))
    if yeni_indirimler:
        mesajlar.append(
            f"🏷️ {baslik}\nYeni kampanya: " + " | ".join(sorted(yeni_indirimler)) +
            f"\nGüncel fiyat: {_fiyat_metni(yeni)}\n{yeni['url']}"
        )

    return mesajlar


def kampanyalari_karsilastir(eski: dict, yeni: dict) -> list[str]:
    """Site geneli kampanyaları karşılaştırır; yeni görülenler için mesaj üretir.

    eski/yeni: {"site": [kampanya, ...]}. Yeni değeri None olan site atlanır
    (sayfa okunamamıştır); ilk çalıştırmada mevcut liste bilgi olarak gönderilir.
    """
    mesajlar = []
    for site, liste in yeni.items():
        if liste is None:
            continue
        site_ad = SITE_ADLARI.get(site, site)
        if site not in eski:  # ilk kontrol: mevcut kampanyaları duyur
            if liste:
                mesajlar.append(f"🎟️ <b>{site_ad} — güncel site kampanyaları</b>\n• " + "\n• ".join(liste))
            continue
        yeni_olanlar = [k for k in liste if k not in (eski.get(site) or [])]
        if yeni_olanlar:
            mesajlar.append(f"🎟️ <b>{site_ad} — YENİ site kampanyası</b>\n• " + "\n• ".join(yeni_olanlar))
    return mesajlar


def gunluk_ozet(oteller: list[dict], kayitlar: list[dict], kampanyalar: dict | None = None) -> str:
    """Tüm otellerin güncel durumunu tek mesajda özetler."""
    from . import depo

    satirlar = ["📋 <b>Günlük Fiyat Özeti</b>"]
    for otel in oteller:
        satirlar.append(f"\n🏨 <b>{otel['ad']}</b> ({otel.get('giris', '?')} → {otel.get('cikis', '?')})")
        for kaynak in otel["kaynaklar"]:
            site_ad = SITE_ADLARI.get(kaynak["site"], kaynak["site"])
            son = depo.son_basarili(kayitlar, otel["id"], kaynak["site"])
            if son:
                satir = f"  • {site_ad}: {_fiyat_metni(son)}"
                if son.get("indirimler"):
                    satir += " 🏷️ " + " | ".join(son["indirimler"][:2])
            else:
                satir = f"  • {site_ad}: veri yok ⚠️"
            satirlar.append(satir)

    if kampanyalar:
        aktifler = [(SITE_ADLARI.get(s, s), liste) for s, liste in kampanyalar.items() if liste]
        if aktifler:
            satirlar.append("\n🎟️ <b>Site kampanyaları</b>")
            for site_ad, liste in aktifler:
                for k in liste[:3]:
                    satirlar.append(f"  • {site_ad}: {k}")
    return "\n".join(satirlar)

"""Ana akış: yapılandırmayı oku → fiyatları çek → karşılaştır → kaydet → bildir.

Kullanım:
  python -m src.main            # normal çalıştırma (Telegram bildirimli)
  python -m src.main --test     # Telegram'a göndermez, mesajları konsola yazar
  python -m src.main --ozet     # kontrol + günlük özet mesajı
"""

import argparse
import time
from datetime import datetime, timezone
from pathlib import Path

import yaml

from . import analiz, bildirim, depo
from .siteler import hotelscom, obilet

SITELER = {"obilet": obilet, "hotelscom": hotelscom}
AYAR_DOSYASI = Path(__file__).resolve().parent.parent / "config" / "oteller.yaml"


def calistir(test_modu: bool = False, ozet: bool = False) -> None:
    ayar = yaml.safe_load(AYAR_DOSYASI.read_text(encoding="utf-8"))
    ayarlar, oteller = ayar["ayarlar"], ayar["oteller"]
    kayitlar = depo.yukle()
    zaman = datetime.now(timezone.utc).isoformat(timespec="seconds")
    mesajlar: list[str] = []

    for otel in oteller:
        for kaynak in otel["kaynaklar"]:
            site, url = kaynak["site"], kaynak["url"]
            if site not in SITELER or not url.startswith("http"):
                print(f"[atlandı] {otel['id']} / {site}: geçerli URL yok")
                continue

            print(f"[kontrol] {otel['ad']} / {site} ...")
            sonuc = SITELER[site].fiyat_cek(url)
            print(f"   fiyat={sonuc['fiyat']} indirimler={sonuc['indirimler']} hata={sonuc['hata']}")

            onceki = depo.son_basarili(kayitlar, otel["id"], site)
            onceki_herhangi = depo.son_kayit(kayitlar, otel["id"], site)
            yeni_kayit = {
                "zaman": zaman,
                "otel_id": otel["id"],
                "otel_ad": otel["ad"],
                "giris": otel.get("giris"),
                "cikis": otel.get("cikis"),
                "site": site,
                "url": url,
                "fiyat": sonuc["fiyat"],
                "indirimler": sonuc["indirimler"],
                "hata": sonuc["hata"],
            }
            mesajlar += analiz.karsilastir(otel, site, onceki, onceki_herhangi, yeni_kayit, ayarlar)
            kayitlar.append(yeni_kayit)
            time.sleep(3)  # siteler arası nazik bekleme

    depo.kaydet(kayitlar)

    if ozet:
        mesajlar.append(analiz.gunluk_ozet(oteller, kayitlar))

    if not mesajlar:
        print("Bildirilecek değişiklik yok.")
        return

    metin = "\n\n".join(mesajlar)
    if test_modu:
        print("\n--- TEST MODU: Telegram'a gönderilmedi ---\n" + metin)
    else:
        bildirim.gonder(metin)
        print("Bildirim gönderildi.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Otel fiyat takip")
    parser.add_argument("--test", action="store_true", help="Telegram'a göndermeden konsola yaz")
    parser.add_argument("--ozet", action="store_true", help="Günlük özet mesajı da gönder")
    args = parser.parse_args()
    calistir(test_modu=args.test, ozet=args.ozet)

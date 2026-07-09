"""Fiyat geçmişi deposu: data/price_history.json okuma/yazma.

Panel de aynı dosyayı okusun diye docs/ altına bir kopya yazılır
(GitHub Pages yalnızca docs/ klasörünü yayınlar).
"""

import json
from pathlib import Path

KOK = Path(__file__).resolve().parent.parent
VERI_DOSYASI = KOK / "data" / "price_history.json"
PANEL_KOPYASI = KOK / "docs" / "price_history.json"


def yukle() -> list[dict]:
    if not VERI_DOSYASI.exists():
        return []
    return json.loads(VERI_DOSYASI.read_text(encoding="utf-8"))


def kaydet(kayitlar: list[dict]) -> None:
    icerik = json.dumps(kayitlar, ensure_ascii=False, indent=1)
    VERI_DOSYASI.parent.mkdir(parents=True, exist_ok=True)
    VERI_DOSYASI.write_text(icerik, encoding="utf-8")
    PANEL_KOPYASI.parent.mkdir(parents=True, exist_ok=True)
    PANEL_KOPYASI.write_text(icerik, encoding="utf-8")


def son_kayit(kayitlar: list[dict], otel_id: str, site: str) -> dict | None:
    """Bu otel+site için en son kayıt (hatalılar dahil)."""
    for k in reversed(kayitlar):
        if k["otel_id"] == otel_id and k["site"] == site:
            return k
    return None


def son_basarili(kayitlar: list[dict], otel_id: str, site: str) -> dict | None:
    """Bu otel+site için fiyatı okunabilmiş en son kayıt."""
    for k in reversed(kayitlar):
        if k["otel_id"] == otel_id and k["site"] == site and k.get("fiyat"):
            return k
    return None

"""Hotels.com otel sayfası adaptörü.

Hotels.com güçlü bot koruması kullanır; daha uzun bekleme süresiyle
genel adaptör denenir. Engellenirse alternatif site adaptörüne geçilecek
(bkz. PROJE.md — Riskler).
"""

from . import ortak


def fiyat_cek(url: str) -> dict:
    return ortak.genel_fiyat_cek(url, bekle_saniye=12)

"""Obilet otel sayfası adaptörü.

Şimdilik genel adaptörü kullanır (sayfadaki en düşük oda fiyatı).
Gerçek otel linki geldiğinde gerekirse site-özel seçiciler eklenecek.
"""

from . import ortak


def fiyat_cek(url: str) -> dict:
    return ortak.genel_fiyat_cek(url, bekle_saniye=8)

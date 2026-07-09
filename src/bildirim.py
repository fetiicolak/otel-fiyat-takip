"""Telegram Bot API ile bildirim gönderimi.

Gerekli ortam değişkenleri (yerelde .env dosyasından da okunur):
  TELEGRAM_BOT_TOKEN  : BotFather'dan alınan token
  TELEGRAM_CHAT_IDS   : virgülle ayrık chat ID listesi (2 kullanıcı)
"""

import os
from pathlib import Path

import requests

API = "https://api.telegram.org/bot{token}/sendMessage"


def _env_yukle() -> None:
    """Yerel geliştirme için basit .env okuyucu."""
    env = Path(__file__).resolve().parent.parent / ".env"
    if not env.exists():
        return
    for satir in env.read_text(encoding="utf-8").splitlines():
        satir = satir.strip()
        if satir and not satir.startswith("#") and "=" in satir:
            anahtar, _, deger = satir.partition("=")
            os.environ.setdefault(anahtar.strip(), deger.strip())


def gonder(mesaj: str) -> None:
    """Mesajı tanımlı tüm chat ID'lere gönderir."""
    _env_yukle()
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_ids = [c.strip() for c in os.environ.get("TELEGRAM_CHAT_IDS", "").split(",") if c.strip()]
    if not token or not chat_ids:
        raise RuntimeError("TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_IDS tanımlı değil")

    for chat_id in chat_ids:
        yanit = requests.post(
            API.format(token=token),
            json={"chat_id": chat_id, "text": mesaj, "parse_mode": "HTML",
                  "disable_web_page_preview": True},
            timeout=30,
        )
        if not yanit.ok:
            print(f"Telegram gönderim hatası ({chat_id}): {yanit.text}")

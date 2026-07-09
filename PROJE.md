# Otel Fiyat Takip Sistemi

## Amaç

İki kullanıcının (Feti ve arkadaşı) rezervasyon yapmayı planladığı **2 oteli** (Marin Otel ve Atrium Otel, Çeşme), **Obilet ve Etstur** üzerinden **4 saatte bir** otomatik kontrol eden; fiyat düşüşlerinde, yeni indirim/kampanyalarda ve belirgin fiyat artışlarında her iki kullanıcıya **Telegram** üzerinden anlık bildirim gönderen bir sistem.

Sistem tamamen bulutta (**GitHub Actions**) çalışır — bilgisayar kapalıyken de 7/24 aktiftir. Fiyat geçmişi, **GitHub Pages** üzerinde yayınlanan tek sayfalık basit bir web panelinde grafikle görüntülenir.

## Mimari

```
GitHub Actions (4 saatte bir cron)
        │
        ▼
  src/main.py ──► siteler/obilet.py ────┐
        │    └──► siteler/etstur.py ────┤  Playwright (headless Chromium)
        │                               │  ile fiyat + indirim çekilir
        ▼                               ▼
  src/analiz.py  ◄── data/price_history.json (önceki kayıtlar)
        │
        ├── değişiklik varsa ──► src/bildirim.py ──► Telegram (2 kullanıcı)
        │
        ▼
  data/price_history.json + docs/price_history.json (Action commit eder)
        │
        ▼
  GitHub Pages paneli (docs/index.html) — güncel fiyatlar + geçmiş grafiği
```

## Teknolojiler

| Bileşen | Teknoloji |
|---|---|
| Zamanlayıcı / barındırma | GitHub Actions (ücretsiz, cron: 4 saatte bir) |
| Fiyat çekme | Python 3.12 + Playwright (headless Chromium) |
| Veri saklama | Repo içinde JSON (`data/price_history.json`) |
| Bildirim | Telegram Bot API |
| Web paneli | Statik HTML + Chart.js, GitHub Pages |

## Bildirim Kuralları

- 🔻 **Fiyat düşüşü**: Eşik aşılırsa bildirim (varsayılan: %3 veya 250 TL — `config/oteller.yaml`'dan ayarlanır)
- 🏷️ **Yeni indirim/kampanya**: Sayfada daha önce görülmeyen kampanya metni belirirse bildirim
- 🔺 **Belirgin fiyat artışı**: Aynı eşiklerle bilgilendirme
- ⚠️ **Okuma hatası**: Bir site okunamazsa (bot koruması vb.) tek seferlik uyarı
- 📋 **Günlük özet**: Her sabah 09:00'da (TR saati) tüm otellerin güncel durumu

> Not: Takip edilen fiyat, sayfadaki **en düşük oda fiyatıdır** (mantık: en ucuz uygun oda).

## Yapılandırma

Otel bilgileri `config/oteller.yaml` dosyasındadır: otel adı, site linkleri (tarih ve kişi sayısı seçili arama sonucu linki), bildirim eşikleri.

Gizli bilgiler GitHub Secrets'ta tutulur (kod içinde YOKTUR):
- `TELEGRAM_BOT_TOKEN` — BotFather'dan alınan bot anahtarı
- `TELEGRAM_CHAT_IDS` — iki kullanıcının chat ID'leri (virgülle ayrık)

## Riskler

- **hotels.com bot koruması** (yaşandı, Temmuz 2026): Akamai koruması headless tarayıcıyı bağlantı seviyesinde engelledi; GitHub Actions'ın veri merkezi IP'lerinde durum daha da kötü olurdu. Bu yüzden hotels.com yerine **Etstur** adaptörü kullanılıyor (aynı oteller, tutarlı fiyatlar + zengin kupon bilgisi). `siteler/hotelscom.py` ileride gerekirse diye repoda duruyor ama yapılandırmada kullanılmıyor.
- **Site tasarım değişikliği**: Scraper fiyat bulamazsa sistem çökmez, Telegram'a uyarı düşer. Obilet'te fiyat yalnızca oda listesi bölgesinden (son "Odayı Seç" öncesi) okunur; Etstur'da başlıktaki "… TL / Odaları Gör" fiyatı esas alınır.

## Kullanım

```bash
# Yerel tek seferlik test (Telegram'a göndermeden, konsola yazar)
python -m src.main --test

# Gerçek çalıştırma (Telegram bildirimli)
python -m src.main

# Günlük özet gönder
python -m src.main --ozet
```

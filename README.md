# 🏨 Otel Fiyat Takip

İki otelin fiyatlarını Obilet ve Etstur üzerinden 4 saatte bir kontrol eder; fiyat düşüşü, yeni kampanya ve belirgin artışlarda **Telegram** ile bildirim gönderir. GitHub Actions üzerinde 7/24 çalışır, fiyat geçmişi **GitHub Pages** panelinde grafikle görünür.

Detaylı mimari için: [PROJE.md](PROJE.md)

## Kurulum

### 1. Otel bilgilerini girin

`config/oteller.yaml` dosyasını açın; otel adlarını ve site linklerini doldurun.
Linki alırken sitede **tarih ve kişi sayısını seçtikten sonra** adres çubuğundaki URL'yi kopyalayın.

### 2. Telegram botu oluşturun (~5 dk)

1. Telegram'da **@BotFather**'a yazın → `/newbot` → bota bir ad ve kullanıcı adı verin.
2. BotFather'ın verdiği **token**'ı kaydedin (örn. `123456:ABC-DEF...`).
3. Siz ve arkadaşınız botunuza Telegram'dan **/start** yazın (bot size mesaj atabilsin diye zorunlu).
4. Chat ID'lerinizi öğrenin: tarayıcıda şu adresi açın (TOKEN yerine kendi token'ınız):
   `https://api.telegram.org/botTOKEN/getUpdates`
   → `"chat":{"id":123456789...` alanındaki sayılar chat ID'lerinizdir.

### 3. Yerel test (isteğe bağlı)

```bash
pip install -r requirements.txt
playwright install chromium
python -m src.main --test        # Telegram'a göndermeden dener
```

Telegram'lı test için proje kökünde `.env` dosyası oluşturun:

```
TELEGRAM_BOT_TOKEN=123456:ABC-DEF...
TELEGRAM_CHAT_IDS=111111111,222222222
```

### 4. GitHub'a yükleyin

1. GitHub'da **public** bir repo oluşturun (GitHub Pages ücretsiz hesapta yalnızca public repolarda çalışır; kodda gizli bilgi yoktur, token'lar Secrets'ta durur).
2. Repo → **Settings → Secrets and variables → Actions** → iki secret ekleyin:
   - `TELEGRAM_BOT_TOKEN`
   - `TELEGRAM_CHAT_IDS` (virgülle ayrık: `111111111,222222222`)
3. Repo → **Settings → Pages** → Source: `Deploy from a branch`, Branch: `main`, Folder: `/docs`.
4. Repo → **Actions** sekmesi → "Fiyat Kontrol" → **Run workflow** ile ilk çalıştırmayı elle tetikleyin.

### 5. Panel

Pages açıldıktan birkaç dakika sonra paneliniz şu adreste olur:
`https://KULLANICI_ADINIZ.github.io/REPO_ADI/`

## Zamanlama

- Her 4 saatte bir fiyat kontrolü (`0 */4 * * *` UTC)
- Her sabah 09:00'da (TR) günlük özet mesajı

## Sorun Giderme

- **"Sayfada fiyat bulunamadı"**: Site bot korumasına takılmış olabilir. Birkaç çalıştırma üst üste başarısızsa alternatif aracı site (Etstur, Otelz) adaptörü eklenebilir.
- **Telegram mesajı gelmiyor**: Botunuza `/start` yazdığınızdan ve chat ID'lerin doğru olduğundan emin olun.

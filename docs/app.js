const SITE_ADLARI = { obilet: "Obilet", hotelscom: "Hotels.com", etstur: "Etstur" };
const RENKLER = ["#2563eb", "#f59e0b", "#10b981", "#8b5cf6"];

const tl = (f) => f.toLocaleString("tr-TR", { maximumFractionDigits: 0 }) + " TL";

async function yukle() {
  let kayitlar;
  try {
    const yanit = await fetch("price_history.json", { cache: "no-store" });
    kayitlar = await yanit.json();
  } catch {
    document.getElementById("guncelleme").textContent = "Veri dosyası bulunamadı — ilk kontrol henüz çalışmamış olabilir.";
    return;
  }
  if (!kayitlar.length) {
    document.getElementById("guncelleme").textContent = "Henüz kayıt yok.";
    return;
  }

  const sonZaman = new Date(kayitlar[kayitlar.length - 1].zaman);
  document.getElementById("guncelleme").textContent =
    "Son kontrol: " + sonZaman.toLocaleString("tr-TR", { dateStyle: "medium", timeStyle: "short" });

  // Kayıtları otele göre grupla
  const oteller = new Map();
  for (const k of kayitlar) {
    if (!oteller.has(k.otel_id)) oteller.set(k.otel_id, { ad: k.otel_ad, kayitlar: [] });
    oteller.get(k.otel_id).kayitlar.push(k);
  }

  const kok = document.getElementById("oteller");
  for (const [otelId, otel] of oteller) {
    const kart = document.createElement("div");
    kart.className = "kart";

    // Site başına son başarılı kayıt + bir önceki (değişim oku için)
    const siteler = new Map();
    for (const k of otel.kayitlar) {
      if (!siteler.has(k.site)) siteler.set(k.site, []);
      if (k.fiyat) siteler.get(k.site).push(k);
    }

    let fiyatHtml = "";
    let indirimHtml = "";
    for (const [site, liste] of siteler) {
      const ad = SITE_ADLARI[site] || site;
      if (!liste.length) { fiyatHtml += kutu(ad, `<span class="hata">veri yok</span>`, ""); continue; }
      const son = liste[liste.length - 1];
      const onceki = liste.length > 1 ? liste[liste.length - 2] : null;
      let degisim = "";
      if (onceki && onceki.fiyat !== son.fiyat) {
        const yuzde = ((son.fiyat - onceki.fiyat) / onceki.fiyat * 100).toFixed(1);
        degisim = son.fiyat < onceki.fiyat
          ? `<span class="degisim dusuk">▼ %${Math.abs(yuzde)}</span>`
          : `<span class="degisim yuksek">▲ %${yuzde}</span>`;
      }
      const normal = son.normal_fiyat ? `<span class="normal-fiyat">${tl(son.normal_fiyat)}</span>` : "";
      fiyatHtml += kutu(ad, `<span class="tutar">${tl(son.fiyat)}</span>${normal}`, degisim, son.url);
      if (son.indirimler?.length) {
        indirimHtml += `<div class="indirimler">🏷️ <b>${ad}:</b> ${son.indirimler.join(" · ")}</div>`;
      }
    }

    const ilk = otel.kayitlar[0];
    kart.innerHTML = `
      <h2>${otel.ad}</h2>
      <div class="tarih">${ilk.giris ? "📅 " + ilk.giris + " → " + (ilk.cikis || "?") : ""}</div>
      <div class="fiyatlar">${fiyatHtml}</div>
      ${indirimHtml}
      <canvas id="grafik-${otelId}" height="110"></canvas>`;
    kok.appendChild(kart);

    ciz(otelId, siteler);
  }

  await kampanyalariGoster(kok);
}

async function kampanyalariGoster(kok) {
  let kampanyalar;
  try {
    const yanit = await fetch("kampanyalar.json", { cache: "no-store" });
    kampanyalar = await yanit.json();
  } catch {
    return; // dosya yoksa kartı gösterme
  }
  const satirlar = [];
  for (const [site, liste] of Object.entries(kampanyalar)) {
    for (const k of liste || []) {
      satirlar.push(`<li><b>${SITE_ADLARI[site] || site}:</b> ${k}</li>`);
    }
  }
  if (!satirlar.length) return;
  const kart = document.createElement("div");
  kart.className = "kart";
  kart.innerHTML = `<h2>🎟️ Site Kampanyaları</h2>
    <ul style="margin:10px 0 0 18px; font-size:.9rem; line-height:1.7">${satirlar.join("")}</ul>`;
  kok.appendChild(kart);
}

function kutu(ad, icerik, degisim, url) {
  const link = url ? `<a class="link" href="${url}" target="_blank" rel="noopener">siteye git →</a>` : "";
  return `<div class="fiyat-kutu">
    <div class="site-ad">${ad}</div>
    <div>${icerik} ${degisim}</div>${link}
  </div>`;
}

function ciz(otelId, siteler) {
  const setler = [];
  let i = 0;
  for (const [site, liste] of siteler) {
    if (!liste.length) continue;
    setler.push({
      label: SITE_ADLARI[site] || site,
      data: liste.map(k => ({ x: k.zaman, y: k.fiyat })),
      borderColor: RENKLER[i % RENKLER.length],
      backgroundColor: RENKLER[i % RENKLER.length],
      tension: 0.25,
      pointRadius: 2,
    });
    i++;
  }
  // Zaman ekseni: kayıt zamanlarını kısa etikete çevir (ek eklenti gerektirmemesi için kategori ekseni)
  const etiketler = [...new Set(setler.flatMap(s => s.data.map(n => n.x)))].sort();
  const kisa = z => new Date(z).toLocaleString("tr-TR", { day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit" });

  new Chart(document.getElementById("grafik-" + otelId), {
    type: "line",
    data: {
      labels: etiketler.map(kisa),
      datasets: setler.map(s => ({
        ...s,
        data: etiketler.map(e => {
          const n = s.data.find(d => d.x === e);
          return n ? n.y : null;
        }),
        spanGaps: true,
      })),
    },
    options: {
      responsive: true,
      plugins: { legend: { labels: { boxWidth: 12 } } },
      scales: {
        y: { ticks: { callback: v => tl(v) } },
        x: { ticks: { maxTicksLimit: 8 } },
      },
    },
  });
}

yukle();

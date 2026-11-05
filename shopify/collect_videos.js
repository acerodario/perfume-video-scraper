// Recolecta los videos de producto de una tienda Shopify.
//
// Uso: abrir cualquier página de la tienda, F12 → Console, pegar y Enter.
// Recorre /products.json, abre /products/<handle>.js de cada producto (el único
// endpoint público que trae `media` con los videos) y descarga shopify_videos.json
// con el MP4 de mayor resolución de cada video. Respeta `retry-after` en los 429.
(async () => {
  const DELAY_MS = 1500;
  const sleep = ms => new Promise(r => setTimeout(r, ms));

  async function get(url) {
    for (let i = 0; i < 5; i++) {
      const r = await fetch(url, {credentials: 'same-origin'});
      if (r.status === 429) {
        const s = +(r.headers.get('retry-after') || 60);
        console.log(`429 en ${url}, esperando ${s}s`);
        await sleep(s * 1000);
        continue;
      }
      if (!r.ok) throw new Error(`${r.status} ${url}`);
      return r.json();
    }
    throw new Error(`demasiados 429: ${url}`);
  }

  const handles = [];
  for (let page = 1; ; page++) {
    const {products} = await get(`/products.json?limit=250&page=${page}`);
    if (!products.length) break;
    handles.push(...products.map(p => p.handle));
    console.log(`página ${page}: ${handles.length} productos`);
    await sleep(1000);
  }

  const videos = [];
  const externos = [];
  for (const [i, h] of handles.entries()) {
    try {
      const p = await get(`/products/${h}.js`);
      for (const m of p.media || []) {
        if (m.media_type === 'video') {
          const mp4 = (m.sources || [])
            .filter(s => s.format === 'mp4')
            .sort((a, b) => b.height - a.height)[0];
          if (mp4) videos.push({handle: h, title: p.title, url: mp4.url,
                                width: mp4.width, height: mp4.height, duration_ms: m.duration});
        } else if (m.media_type === 'external_video') {
          externos.push({handle: h, title: p.title, host: m.host, id: m.external_id});
        }
      }
    } catch (e) {
      console.warn(h, e.message);
    }
    console.log(`${i + 1}/${handles.length} ${h} — ${videos.length} videos`);
    await sleep(DELAY_MS);
  }

  const blob = new Blob([JSON.stringify({store: location.host, videos, externos}, null, 2)],
                        {type: 'application/json'});
  const a = Object.assign(document.createElement('a'),
                          {href: URL.createObjectURL(blob), download: 'shopify_videos.json'});
  a.click();
  console.log(`Listo: ${videos.length} videos MP4, ${externos.length} externos (YouTube/Vimeo)`);
})();

# perfume-video-scraper

Herramientas para extraer los videos de producto de tiendas de perfumes en línea, en la mayor resolución que publique cada sitio. Las hice para conseguir material audiovisual de fichas de producto en un catálogo de e-commerce.

*Tools to extract product videos from fragrance e-commerce sites (Shopify storefronts and Carolina Herrera's Next.js storefront) at the highest available resolution.*

| Carpeta | Plataforma | Técnica |
|---|---|---|
| [`shopify/`](shopify/) | Cualquier tienda Shopify (probado con Afnan UK) | API pública `products.json` + `/products/<handle>.js`, ejecutada desde el navegador |
| [`puig/`](puig/) | Carolina Herrera (Puig) | Parseo del payload JSON incrustado en el HTML + descarga de HLS (Cloudflare Stream) |

## Shopify

En Shopify, `products.json` lista el catálogo, pero no trae los videos. Para eso hay que abrir el `.js` de cada producto, que incluye el campo `media` con todas las fuentes de cada video (MP4 en 480p, 720p y 1080p, más un HLS).

Algunas tiendas limitan con `429` a los clientes que no son navegadores. Por eso la recolección corre en la consola del navegador, en el mismo origen de la tienda y a un ritmo de una petición cada 1,5 s. Si llega un 429, espera lo que diga `retry-after`. La descarga se hace después desde `cdn.shopify.com`.

```text
1. Abrir la tienda → F12 → Console → pegar shopify/collect_videos.js
   → se descarga shopify_videos.json
2. python shopify/download_videos.py shopify_videos.json -o videos
```

- Elige el MP4 de mayor altura de cada video.
- Nombra los archivos con el handle del producto (`9-am-dive.mp4`, `9-am-dive_2.mp4`…).
- Se puede volver a correr sin duplicar, porque salta los archivos que ya existen.
- Los videos externos (YouTube/Vimeo) se listan aparte.

## Puig / Carolina Herrera

La ficha de producto es una app de Next.js que serializa los datos del producto dentro del HTML, con las comillas escapadas. El script:

1. Desescapa el payload y busca los objetos planos con `"type":"video"`.
2. Filtra por el `sku` de la URL, porque la página también trae medios de otros productos.
3. Ordena por `galleryIndex` y descarga los MP4 del servidor de medios.
4. Con `--campaign`, también baja los videos de campaña del CMS (HLS en Cloudflare Stream), eligiendo la variante de mayor resolución del master playlist.

```bash
python puig/puig_videos.py "https://www.carolinaherrera.com/ae/en/p-fragrance/labomba?sku=000000000065195954" --campaign -o videos
python puig/puig_videos.py URL --list   # solo listar
```

Resultado con La Bomba: 2 videos de galería en 1080×1350, campaña en 1920×1080 y su versión vertical en 1080×1920.

## Requisitos

- Python 3.9+ (solo biblioteca estándar)
- Para HLS: [yt-dlp](https://github.com/yt-dlp/yt-dlp) (recomendado) o ffmpeg

## Uso responsable

- Solo accede a datos públicos de fichas de producto, a ritmo bajo y respetando `retry-after`.
- No intenta saltarse protecciones anti-bot ni usar endpoints privados.
- Los videos son propiedad de cada marca. Antes de publicarlos, revisa que tengas permiso de uso, por ejemplo como distribuidor autorizado.

---

León Darío Acero Zapata · [LinkedIn](https://www.linkedin.com/in/dario-acero) · Web Scraping & Data Developer

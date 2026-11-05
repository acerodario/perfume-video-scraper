"""Extrae y descarga los videos de una ficha de producto de Carolina Herrera.

La página trae los datos del producto serializados dentro del HTML (payload de
Next.js con las comillas escapadas). Ahí cada elemento de la galería es un objeto
plano con "type":"video", "galleryIndex" y la URL del MP4 en el servidor de medios.
Los videos de campaña del CMS van aparte, como HLS en Cloudflare Stream.

Uso:
    python puig_videos.py "https://www.carolinaherrera.com/ae/en/p-fragrance/labomba?sku=000000000065195954"
    python puig_videos.py URL -o videos --campaign      # incluye los videos de campaña (HLS)
    python puig_videos.py URL --list                    # solo lista, no descarga

Los HLS se bajan con yt-dlp (mejor calidad) y, si no está instalado, con ffmpeg.
"""
import argparse
import json
import re
import shutil
import subprocess
import urllib.parse
import urllib.request
from pathlib import Path

UA = "puig-videos/1.0 (+https://github.com/acerodario)"
# Objetos JSON sin llaves anidadas: así quedan los items de la galería.
FLAT_OBJ = re.compile(r"\{[^{}]*\}")
HLS = re.compile(r'"(?:url|mobileUrl)":"(https://[^"]+cloudflarestream\.com/[^"]+\.m3u8)"')


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", errors="replace")


def download(url, destino):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    tmp = destino.with_suffix(".part")
    with urllib.request.urlopen(req, timeout=60) as r, open(tmp, "wb") as f:
        shutil.copyfileobj(r, f)
    tmp.rename(destino)


def gallery_videos(html, base, sku):
    text = html.replace('\\"', '"')
    vistos, videos = set(), []
    for m in FLAT_OBJ.finditer(text):
        chunk = m.group(0)
        if '"type":"video"' not in chunk:
            continue
        try:
            obj = json.loads(chunk)
        except json.JSONDecodeError:
            continue
        # Con sku, quedarse solo con los medios de ese producto (la página trae otros).
        if sku and not str(obj.get("id", "")).startswith(sku):
            continue
        url = urllib.parse.urljoin(base, obj["url"])
        if url in vistos:
            continue
        vistos.add(url)
        videos.append({"index": obj.get("galleryIndex"), "alt": obj.get("altText", ""),
                       "size": obj.get("size"), "url": url})
    return sorted(videos, key=lambda v: v["index"] if v["index"] is not None else 999)


def campaign_videos(html):
    text = html.replace('\\"', '"')
    return list(dict.fromkeys(HLS.findall(text)))


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-") or "producto"


def download_hls(url, destino):
    if shutil.which("yt-dlp"):
        cmd = ["yt-dlp", "-q", "--no-warnings", "-f", "bv*+ba/b",
               "--merge-output-format", "mp4", "-o", str(destino), url]
    elif shutil.which("ffmpeg"):
        # ffmpeg no elige sola la variante más alta: hay que leer el master playlist.
        variantes = re.findall(r"RESOLUTION=\d+x(\d+)[^\n]*\n([^\n#]+)", fetch(url))
        mejor = max(variantes, key=lambda v: int(v[0]))[1].strip() if variantes else url
        cmd = ["ffmpeg", "-v", "error", "-y", "-i", urllib.parse.urljoin(url, mejor),
               "-c", "copy", str(destino)]
    else:
        raise RuntimeError("se necesita yt-dlp o ffmpeg para los videos HLS")
    subprocess.run(cmd, check=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("url", help="URL de la ficha de producto")
    ap.add_argument("-o", "--out", type=Path, default=Path("videos"), help="carpeta de salida")
    ap.add_argument("--campaign", action="store_true", help="incluir videos de campaña (HLS)")
    ap.add_argument("--list", action="store_true", help="solo listar las URLs")
    args = ap.parse_args()

    parsed = urllib.parse.urlparse(args.url)
    sku = urllib.parse.parse_qs(parsed.query).get("sku", [None])[0]
    nombre = slug(parsed.path.rstrip("/").split("/")[-1])
    html = fetch(args.url)

    galeria = gallery_videos(html, args.url, sku)
    campana = campaign_videos(html) if args.campaign else []
    print(f"{len(galeria)} videos de galería, {len(campana)} de campaña")

    for v in galeria:
        print(f"  [{v['index']}] {v['size']}  {v['url']}")
    for u in campana:
        print(f"  [campaña] {u}")
    if args.list:
        return

    args.out.mkdir(parents=True, exist_ok=True)
    for v in galeria:
        destino = args.out / f"{nombre}_galeria_{v['index']}.mp4"
        if not destino.exists():
            download(v["url"], destino)
        print(f"OK  {destino}")
    for i, u in enumerate(campana, 1):
        destino = args.out / f"{nombre}_campana_{i}.mp4"
        if not destino.exists():
            download_hls(u, destino)
        print(f"OK  {destino}")


if __name__ == "__main__":
    main()

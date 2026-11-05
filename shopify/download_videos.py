"""Descarga los MP4 listados en shopify_videos.json (generado por collect_videos.js).

Uso:
    python download_videos.py shopify_videos.json [-o carpeta_salida]

Nombra cada archivo con el handle del producto (handle.mp4, handle_2.mp4, ...)
y salta los que ya existen, así que se puede volver a correr sin duplicar.
"""
import argparse
import json
import time
import urllib.request
from pathlib import Path


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("json", type=Path, help="archivo generado por collect_videos.js")
    ap.add_argument("-o", "--out", type=Path, default=Path("videos"), help="carpeta de salida")
    args = ap.parse_args()

    data = json.loads(args.json.read_text(encoding="utf-8"))
    args.out.mkdir(parents=True, exist_ok=True)

    usados = {}
    ok = saltados = fallidos = 0
    for v in data["videos"]:
        n = usados[v["handle"]] = usados.get(v["handle"], 0) + 1
        nombre = v["handle"] + (f"_{n}" if n > 1 else "") + ".mp4"
        destino = args.out / nombre
        if destino.exists():
            saltados += 1
            continue
        try:
            tmp = destino.with_suffix(".part")
            urllib.request.urlretrieve(v["url"], tmp)
            tmp.rename(destino)
            ok += 1
            print(f"OK    {nombre}  ({destino.stat().st_size / 1e6:.1f} MB)")
        except Exception as e:
            fallidos += 1
            print(f"FALLO {nombre}: {e}")
        time.sleep(0.3)

    print(f"\nDescargados {ok}, ya existían {saltados}, fallidos {fallidos} -> {args.out.resolve()}")
    for x in data.get("externos", []):
        print(f"Externo (no MP4): {x['handle']} -> {x['host']} {x['id']}")


if __name__ == "__main__":
    main()

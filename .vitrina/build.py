# -*- coding: utf-8 -*-
"""build.py — arma la Vitrina leyendo SOLO el repo. Corre en GitHub Actions, sin una sola llave.

Este es el que enciende la nube. No consulta Cloudinary ni PROD ni git-fetch: lee las carpetas del
repo con `index.html`, sus `meta.json`, y los JSON de config (destinos, portadas). Con eso construye
el manifiesto y arma la página con la MISMA función que el generador local (`construir_pagina`),
así no hay dos diseños (cero drift).

Python puro (stdlib) — no necesita pip install. Pensado para `python build.py` dentro del repo,
disparado por un push (ver .github/workflows/vitrina.yml).

Uso local para probar:  py -3.13 build.py --repo <ruta-al-repo-galerias>
"""
import os
import sys
import json
import datetime

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import gen_vitrina_pagina as pagina   # la MISMA función de armado que usa el local
import portada as _portada


def _opt(n, d=None):
    a = sys.argv[1:]
    return a[a.index(n) + 1] if n in a and a.index(n) + 1 < len(a) else d


def _json(ruta, defecto=None):
    try:
        with open(ruta, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return defecto


def galerias_del_repo(repo):
    """Toda galería publicada (carpeta con index.html) con su ficha meta.json."""
    out = []
    for n in sorted(os.listdir(repo)):
        d = os.path.join(repo, n)
        if n.startswith(".") or not os.path.isdir(d):
            continue
        if not os.path.isfile(os.path.join(d, "index.html")):
            continue
        ficha = _json(os.path.join(d, "meta.json"), {})
        out.append((n, ficha))
    return out


def construir_manifiesto(repo, repo_exp=None):
    """El manifiesto, hecho SOLO con lo que hay en el repo. Una galería sin ficha entra igual
    (no se esconde nada publicado), pero queda anotada para que se le siembre la ficha."""
    curadas = _portada.cargar_curadas()
    por_destino, sin_ficha = {}, []
    for slug, f in galerias_del_repo(repo):
        if not f or not f.get("destino"):
            sin_ficha.append(slug)
            # sin ficha no sabemos el destino sin llaves: va a un cajón visible, no se pierde
            destino = "_sin-clasificar"
            fila = {"slug": slug, "titulo": slug.replace("-", " ").title(), "fotos": 0,
                    "video": False, "portada": _portada.resolver(slug, None, None, curadas)}
        else:
            destino = f["destino"]
            fila = {"slug": slug, "titulo": f.get("titulo") or slug.replace("-", " ").title(),
                    "hotel_cloudinary": f.get("cloudinary", slug),
                    "fotos": f.get("fotos", 0), "video": f.get("video", False),
                    "portada": _portada.resolver(slug, f.get("portada"), None, curadas)}
        fila["url"] = f"https://galerias.trvely.com.co/{slug}/"
        fila["por_ficha"] = bool(f)
        por_destino.setdefault(destino, []).append(fila)
    for d in por_destino:
        por_destino[d].sort(key=lambda h: h["slug"])

    # experiencias: cada destino trae su ficha en su propio repo (o en el JSON de config de respaldo)
    exps = []
    exp_dir = repo_exp or _opt("--repo-exp")
    if exp_dir and os.path.isdir(exp_dir):
        for n in sorted(os.listdir(exp_dir)):
            d = os.path.join(exp_dir, n)
            if os.path.isfile(os.path.join(d, "index.html")):
                f = _json(os.path.join(d, "meta.json"), {})
                e = {"slug": n, "url": f"https://experiencias.trvely.com.co/{n}/"}
                if f.get("fondo"):
                    e["fondo"] = f["fondo"]
                if f.get("titulo"):
                    e["titulo"] = f["titulo"]
                exps.append(e)
    else:
        exps = _json(os.path.join(AQUI, "experiencias_respaldo.json"), [])

    return {"galerias_por_destino": por_destino, "experiencias": exps,
            "sin_ficha": sin_ficha,
            "totales": {"galerias": sum(len(v) for v in por_destino.values()),
                        "experiencias": len(exps)}}


def main():
    repo = _opt("--repo", os.path.dirname(AQUI) if os.path.basename(AQUI) == ".vitrina" else ".")
    doc = construir_manifiesto(repo, _opt("--repo-exp"))

    # la nube corre en UTC; la fecha del pie va en hora de Colombia (UTC-5)
    ahora_co = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=5)
    html = pagina.construir_pagina(doc, hoy=ahora_co.strftime("%d/%m/%Y · %H:%M"))

    salida = _opt("--salida", os.path.join(repo, "index.html"))
    with open(salida, "w", encoding="utf-8") as f:
        f.write(html)

    t = doc["totales"]
    print(f"build.py — {t['galerias']} galerias · {t['experiencias']} experiencias -> {salida}")
    if doc["sin_ficha"]:
        print(f"  OJO: {len(doc['sin_ficha'])} sin ficha meta.json: {', '.join(doc['sin_ficha'][:8])}")
        print("  (entraron sin clasificar; correr goal_vitrina local para sembrarles la ficha)")


if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
"""La portada de una galeria se decide en UN solo sitio y con UN solo orden.

Antes la decision estaba repartida en cuatro fuentes y dos scripts, con precedencias distintas
—el mapa dejaba ganar a Cloudinary, la pagina leia otros dos archivos—. Eso es justo la enfermedad
que la Vitrina vino a curar: dos verdades. Aqui vive la unica.

ORDEN DE AUTORIDAD (de mas a menos):
  1. portadas_manual.json  — lo que una PERSONA eligio a ojo. Manda sobre todo. La portada es una
                             promesa, y ningun puntaje sabe que vende (la medicion corono un bano).
  2. portadas.json         — lo que la MEDICION propuso (color, contraste, mar/piscina).
  3. meta.json (ficha)     — la portada que traia la galeria al publicarse.
  4. Cloudinary _001       — la primera foto, ultimo recurso (a veces es un bano).
"""
import os
import json

AQUI = os.path.dirname(os.path.abspath(__file__))


def _json(nombre):
    try:
        with open(os.path.join(AQUI, nombre), encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def cargar_curadas():
    """Devuelve {slug: public_id} con lo manual y lo medido ya resueltos por autoridad.

    Se carga UNA vez y se pasa a resolver(): no re-abrir los JSON por cada galeria.
    """
    manual = _json("portadas_manual.json")   # {slug: {pid: ...}}
    auto = _json("portadas.json")            # {slug: {propuesta: ...}}
    curadas = {}
    for slug, v in auto.items():
        if v.get("propuesta"):
            curadas[slug] = v["propuesta"]
    for slug, v in manual.items():           # lo manual pisa lo medido
        if v.get("pid"):
            curadas[slug] = v["pid"]
    return curadas


def resolver(slug, ficha_portada=None, cloudinary_portada=None, curadas=None):
    """El public_id de la portada de una galeria, por orden de autoridad. None si no hay ninguna."""
    curadas = curadas if curadas is not None else cargar_curadas()
    return curadas.get(slug) or ficha_portada or cloudinary_portada

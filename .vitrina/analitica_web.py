# -*- coding: utf-8 -*-
"""analitica_web.py — El contador de visitas de Trvely (Cloudflare Web Analytics), en UN solo sitio.

QUE RESPONDE: hasta hoy (27-jul-2026) no sabiamos si ALGUIEN mira lo que construimos. Se sabia
cuantas galerias hay, no cuantas se ven. Esto contesta lo unico que importa:
    ¿que hoteles miran? · ¿que destino de experiencias interesa? · ¿los asesores usan el cotizador?
    ¿de donde llega la gente? · ¿desde el celular o el computador?

POR QUE CLOUDFLARE Y NO GOOGLE: es gratis, no usa cookies y **no sigue a personas** — cuenta
paginas vistas, no individuos. No hay que pedir consentimiento ni poner el banner de cookies, y no
se le entregan los datos de nuestros clientes a nadie. El token NO es un secreto: viaja dentro del
HTML publicado, cualquiera puede verlo. Por eso vive aqui, en el repo, sin problema.

POR QUE EN UN MODULO Y NO PEGADO EN CADA GENERADOR: el 27-jul se perdio el logo del pie en 96
paginas porque vivia en una plantilla suelta que nadie recordaba. Un dato que se copia en varios
sitios se desincroniza; aqui hay UNA fuente y todos la leen.

Uso desde un generador:
    import analitica_web
    html = analitica_web.insertar(html, "galerias.trvely.com.co")

Uso para revisar/instalar en lo ya publicado:
    py -3.13 instalar_analitica.py --seco
"""
import re

# host publicado -> token del beacon (publico, viaja en el HTML)
TOKENS = {
    "galerias.trvely.com.co":     "6c26012f2d8541e88651945942d51d8b",
    "experiencias.trvely.com.co": "e0dce2d410a04096a1ceec22f8d5e40f",
    "cotizador.trvely.com.co":    "95aba214d8b34f6abbf44e90ab09bd39",
}

MARCA = "cloudflareinsights.com/beacon.min.js"
RE_BEACON = re.compile(r"<!-- Cloudflare Web Analytics -->.*?<!-- End Cloudflare Web Analytics -->",
                       re.S)


def snippet(host):
    """El trocito de HTML que cuenta la visita. Devuelve '' si el host no esta registrado."""
    token = TOKENS.get(host)
    if not token:
        return ""
    return ('<!-- Cloudflare Web Analytics -->'
            '<script defer src="https://static.cloudflareinsights.com/beacon.min.js" '
            f'data-cf-beacon=\'{{"token": "{token}"}}\'></script>'
            '<!-- End Cloudflare Web Analytics -->')


def tiene(html):
    """¿Esta pagina ya cuenta sus visitas?"""
    return MARCA in html


def insertar(html, host):
    """Devuelve el HTML con el contador puesto justo antes de </body>. Idempotente.

    Si ya lo tiene se REEMPLAZA (asi un cambio de token se propaga solo al regenerar, en vez de
    dejar dos beacons peleando). Si la pagina no tiene </body>, se deja intacta y se avisa por el
    valor de retorno — nunca se escribe un HTML roto por insistir.
    """
    trozo = snippet(host)
    if not trozo:
        return html
    if tiene(html):
        return RE_BEACON.sub(trozo, html, count=1) if RE_BEACON.search(html) else html
    if "</body>" not in html:
        return html
    return html.replace("</body>", trozo + "</body>", 1)


def host_de(ruta):
    """Adivina a que sitio pertenece un archivo, por el repo en el que vive."""
    p = str(ruta).replace("\\", "/").lower()
    if "trvely-galerias" in p:
        return "galerias.trvely.com.co"
    if "trvely-experiencias" in p:
        return "experiencias.trvely.com.co"
    if "trvely-cotizador" in p:
        return "cotizador.trvely.com.co"
    return None

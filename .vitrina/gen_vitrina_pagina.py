# -*- coding: utf-8 -*-
"""FASE 4 de LA VITRINA: arma la pagina index.html a partir de vitrina.json.

v2 (22-jul-2026) — linea grafica PRO, hermana de experiencias.trvely.com.co/peru: hero burgundy con
TRIANA (la azafata de la marca, recurso del Figma de mails), tipografia de marca (Extenda para
titulares, Montserrat para el cuerpo, White Star para la firma) y tarjetas con foto grande.

Filtros del asesor: destino · tipo (hoteles/experiencias) · solo con video · orden (A-Z o mas fotos)
+ buscador que filtra mientras se escribe. Todo del lado del navegador: la pagina es estatica.

Reglas que respeta: solo entra lo VIVO (http 200) · el destino lo manda PROD (destino_segun_prod) ·
un hotel DESACTIVADO en PROD no aparece · cero precios y costos · noindex · fecha visible.
Assets que espera en el repo: assets/extenda.ttf · assets/whitestar.otf · assets/triana.webp|png

Uso: py -3.13 gen_vitrina_pagina.py [--json vitrina.json] [--salida index.html] [--publicar <repo>]
"""
import os
import sys
import json
import html
import datetime

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import portada as _portada   # una sola funcion decide la portada (misma que usa el mapa)
CLOUD = "https://res.cloudinary.com/trvely/image/upload"
LOGO = "assets/logo-beige.png"   # hv1 (beige #FDEEDB) recortado: el SVG venia en lienzo cuadrado
def _tabla_destinos():
    """Los destinos viven en destinos.json, no en el codigo: uno nuevo se agrega alli y entra solo."""
    try:
        with open(os.path.join(AQUI, "destinos.json"), encoding="utf-8") as f:
            return json.load(f)["destinos"]
    except (OSError, ValueError, KeyError):
        return {}


DESTINOS = _tabla_destinos()
NOMBRE_DESTINO = {k: v.get("nombre", k) for k, v in DESTINOS.items()}
SIGLAS = {"de", "la", "el", "los", "las", "del", "y", "a", "by", "on"}
# Fondo de cada tarjeta de experiencias = el hero que ya usa esa pagina publicada (Peru no tiene
# _hero propio: su portada es Machu Picchu).
def _fondos_experiencias():
    """Foto de fondo de cada destino de experiencias. Primero la que declara su propia ficha
    (meta.json en el repo de experiencias); si no, la tabla de respaldo de destinos.json.
    Un destino de experiencias nuevo entra solo: basta que traiga su ficha."""
    fondos = {}
    for slug, d in DESTINOS.items():
        if d.get("fondo_experiencias"):
            fondos[slug] = d["fondo_experiencias"]
    return fondos


FONDO_EXP = _fondos_experiencias()


def _opt(n, d=None):
    a = sys.argv[1:]
    return a[a.index(n) + 1] if n in a and a.index(n) + 1 < len(a) else d


def bonito(slug):
    return NOMBRE_DESTINO.get(slug, slug.replace("-", " ").title())


def titulo_parejo(t):
    """'ARENA BLANCA' -> 'Arena Blanca'. Los titulos vienen mezclados porque cada galeria se genero
    en su momento; en una sola pagina se nota."""
    if not t or t != t.upper():
        return t
    out = []
    for i, p in enumerate(t.lower().split()):
        if p in ("ghl", "hm"):
            out.append(p.upper())
        elif i and p in SIGLAS:
            out.append(p)
        else:
            out.append(p.capitalize())
    return " ".join(out)


def portada(pid, w=560, h=420):
    return f"{CLOUD}/c_fill,g_auto,w_{w},h_{h},q_auto,f_auto/{pid}" if pid else None


def agrupar(doc):
    """{destino: [galerias vivas]} — PROD manda el destino; lo muerto y lo que no opera no entra."""
    grupos = {}
    for destino, lista in doc["galerias_por_destino"].items():
        for g in lista:
            if not g.get("vivo", True):
                continue
            if (g.get("motivo") or "").startswith("hotel desactivado"):
                continue
            grupos.setdefault(g.get("destino_segun_prod") or destino, []).append(g)
    for d in grupos:
        grupos[d].sort(key=lambda g: titulo_parejo(g["titulo"]).lower())
    return grupos


def tarjeta_hotel(g, destino, curadas=None):
    t = html.escape(titulo_parejo(g["titulo"]))
    dest = html.escape(bonito(destino))
    src = portada(_portada.resolver(g["slug"], g.get("portada"), None, curadas))
    foto = (f'<img loading="lazy" src="{src}" alt="{t}">' if src
            else '<span class="sin-foto">trvely</span>')
    kicker = f'{dest} · {g["fotos"]} fotos' + (" · video" if g.get("video") else "")
    return f"""      <article class="ficha" data-buscar="{html.escape((titulo_parejo(g['titulo']) + ' ' + g['slug'] + ' ' + bonito(destino)).lower())}"
        data-destino="{html.escape(destino)}" data-tipo="hotel" data-video="{1 if g.get('video') else 0}" data-fotos="{g['fotos']}">
        <a class="ficha-foto" href="{g['url']}" target="_blank" rel="noopener">{foto}{'<span class="marca-video">▶ video</span>' if g.get('video') else ''}</a>
        <div class="ficha-cuerpo">
          <p class="kicker">{html.escape(kicker)}</p>
          <h3><a href="{g['url']}" target="_blank" rel="noopener">{t}</a></h3>
          <div class="acciones">
            <button class="btn-copiar" data-url="{g['url']}">Copiar enlace</button>
            <a class="btn-abrir" href="{g['url']}" target="_blank" rel="noopener">Abrir</a>
          </div>
        </div>
      </article>"""


def tarjeta_exp(e):
    d = bonito(e["slug"])
    pid = e.get("fondo") or FONDO_EXP.get(e["slug"])
    fondo = (f' style="background-image:url({CLOUD}/c_fill,g_auto,w_560,h_420,q_auto,f_auto/'
             f'e_improve:outdoor/{pid})"' if pid else "")
    return f"""      <article class="ficha ficha-exp" data-buscar="experiencias {html.escape(d.lower())} {html.escape(e['slug'])}"
        data-destino="{html.escape(e['slug'])}" data-tipo="experiencia" data-video="0" data-fotos="999">
        <a class="ficha-foto exp" href="{e['url']}" target="_blank" rel="noopener"{fondo}>
          <span class="exp-rotulo">Experiencias</span><span class="exp-destino">{html.escape(d)}</span>
        </a>
        <div class="ficha-cuerpo">
          <p class="kicker">Tours y planes</p>
          <h3><a href="{e['url']}" target="_blank" rel="noopener">Experiencias {html.escape(d)}</a></h3>
          <div class="acciones">
            <button class="btn-copiar" data-url="{e['url']}">Copiar enlace</button>
            <a class="btn-abrir" href="{e['url']}" target="_blank" rel="noopener">Abrir</a>
          </div>
        </div>
      </article>"""


def construir_pagina(doc, hoy=None):
    """Arma el HTML de la Vitrina desde el manifiesto. FUNCIÓN PURA: no lee archivos externos ni
    la red, no depende del sistema operativo. La usan el generador local Y build.py (la nube):
    un solo diseño, cero drift. `hoy` se puede inyectar (la nube pasa hora Colombia)."""
    grupos = agrupar(doc)
    curadas = _portada.cargar_curadas()
    exps = [e for e in doc["experiencias"] if e.get("vivo", True)]
    total = sum(len(v) for v in grupos.values())
    fotos = sum(g["fotos"] for v in grupos.values() for g in v)
    orden_dest = sorted(grupos, key=lambda x: (-len(grupos[x]), bonito(x)))

    chips = ['<button class="chip activo" data-filtro-destino="todos">Todos <span>{}</span></button>'
             .format(total + len(exps))]
    chips += ['<button class="chip" data-filtro-destino="experiencias">Experiencias <span>{}</span></button>'
              .format(len(exps))]
    chips += ['<button class="chip" data-filtro-destino="{}">{} <span>{}</span></button>'
              .format(html.escape(d), html.escape(bonito(d)), len(grupos[d])) for d in orden_dest]

    secciones = [f"""    <section class="bloque" data-seccion="experiencias">
      <h2 class="titulo-bloque">Experiencias <span class="cuenta">{len(exps)}</span></h2>
      <div class="rejilla">
{chr(10).join(tarjeta_exp(e) for e in sorted(exps, key=lambda e: bonito(e['slug']).lower()))}
      </div>
    </section>"""]
    for d in orden_dest:
        secciones.append(f"""    <section class="bloque" data-seccion="{html.escape(d)}">
      <h2 class="titulo-bloque">{html.escape(bonito(d))} <span class="cuenta">{len(grupos[d])}</span></h2>
      <div class="rejilla">
{chr(10).join(tarjeta_hotel(g, d, curadas) for g in grupos[d])}
      </div>
    </section>""")

    hoy = hoy or datetime.datetime.now().strftime("%d/%m/%Y · %H:%M")
    pagina = f"""<!doctype html><html lang="es"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,nofollow">
<meta name="theme-color" content="#B41241">
<title>Vitrina Trvely · hoteles y experiencias</title>
<style>
  @font-face {{ font-family:'Extenda'; src:url('assets/extenda.ttf') format('truetype'); font-display:swap; }}
  @font-face {{ font-family:'WhiteStar'; src:url('assets/whitestar.otf') format('opentype'); font-display:swap; }}
  :root {{
    --burg:#B41241; --burg-hondo:#7C0C2C; --beige:#F4E5D2; --crema:#FAF7F2;
    --tinta:#1C1B1A; --gris:#8C8681; --linea:#E9DFD4;
    --sombra:0 1px 2px rgba(28,27,26,.06), 0 8px 24px rgba(28,27,26,.07);
    --sombra-alta:0 2px 4px rgba(28,27,26,.08), 0 18px 40px rgba(124,12,44,.16);
  }}
  * {{ box-sizing:border-box; margin:0; padding:0; }}
  html {{ scroll-behavior:smooth; }}
  body {{ font-family:'Montserrat','Segoe UI',system-ui,sans-serif; background:var(--crema);
          color:var(--tinta); -webkit-font-smoothing:antialiased; }}
  a {{ color:inherit; }}
  ::selection {{ background:var(--beige); }}

  /* ---------- HERO: la banda de marca, con Triana asomando ---------- */
  .hero {{ position:relative; background:linear-gradient(115deg,var(--burg-hondo) 0%,var(--burg) 62%);
           color:#fff; overflow:hidden; }}
  .hero::after {{ content:''; position:absolute; inset:auto 0 -1px 0; height:34px; background:var(--crema);
                  border-radius:34px 34px 0 0; }}
  .hero-caja {{ max-width:1220px; margin:0 auto; padding:26px 22px 58px; display:grid;
                grid-template-columns:minmax(0,1fr) 300px; gap:16px; align-items:end; }}
  .logo {{ height:34px; opacity:.97; }}
  .eyebrow {{ margin:30px 0 10px; font-size:11.5px; letter-spacing:.16em; text-transform:uppercase;
              color:var(--beige); font-weight:700; }}
  /* Extenda es una display muy alta: con line-height < 1 los remates se cortan arriba. */
  .hero h1 {{ font-family:'Extenda','Montserrat',sans-serif; font-weight:400;
              font-size:clamp(44px,7.4vw,84px); line-height:1.06; letter-spacing:1.5px; }}
  .firma {{ font-family:'WhiteStar','Segoe Script',cursive; color:var(--beige);
            font-size:clamp(26px,3.6vw,40px); line-height:1; margin:2px 0 0 4px; }}
  .buscar {{ position:relative; margin-top:24px; max-width:520px; }}
  .buscar input {{ width:100%; padding:15px 20px 15px 48px; border:0; border-radius:30px;
                   font:inherit; font-size:15.5px; color:var(--tinta); background:#fff;
                   box-shadow:0 10px 30px rgba(0,0,0,.16); }}
  .buscar input:focus {{ outline:3px solid var(--beige); outline-offset:2px; }}
  .buscar .lupa {{ position:absolute; left:19px; top:50%; transform:translateY(-50%); opacity:.45; }}
  .triana {{ align-self:end; justify-self:end; margin-bottom:-58px; width:300px; max-width:100%;
             filter:drop-shadow(0 22px 34px rgba(0,0,0,.3)); }}

  /* ---------- FILTROS ---------- */
  .filtros {{ position:sticky; top:0; z-index:20; background:rgba(250,247,242,.94);
              backdrop-filter:blur(10px); border-bottom:1px solid var(--linea); }}
  .filtros-caja {{ max-width:1220px; margin:0 auto; padding:12px 22px; }}
  .chips {{ display:flex; gap:8px; overflow-x:auto; padding-bottom:2px; scrollbar-width:none; }}
  .chips::-webkit-scrollbar {{ display:none; }}
  .chip {{ flex:0 0 auto; border:1.5px solid var(--linea); background:#fff; color:var(--tinta);
           border-radius:22px; padding:9px 15px; font:inherit; font-size:13px; font-weight:700;
           cursor:pointer; transition:background .18s, color .18s, border-color .18s; }}
  .chip span {{ font-weight:600; opacity:.5; font-size:11.5px; margin-left:3px; }}
  .chip:hover {{ border-color:var(--burg); color:var(--burg); }}
  .chip.activo {{ background:var(--burg); border-color:var(--burg); color:#fff; }}
  .chip.activo span {{ opacity:.72; }}
  .afinar {{ display:flex; align-items:center; gap:14px; flex-wrap:wrap; margin-top:10px;
             font-size:12.5px; color:var(--gris); }}
  .interruptor {{ display:inline-flex; align-items:center; gap:7px; cursor:pointer; font-weight:600; }}
  .interruptor input {{ accent-color:var(--burg); width:16px; height:16px; }}
  .orden {{ margin-left:auto; display:inline-flex; align-items:center; gap:7px; font-weight:600; }}
  .orden select {{ font:inherit; font-size:12.5px; font-weight:700; color:var(--tinta);
                   border:1.5px solid var(--linea); background:#fff; border-radius:16px;
                   padding:6px 10px; cursor:pointer; }}

  /* ---------- CONTENIDO ---------- */
  main {{ max-width:1220px; margin:0 auto; padding:6px 22px 60px; }}
  .titulo-bloque {{ font-family:'Extenda','Montserrat',sans-serif; font-weight:400; font-size:28px;
                    letter-spacing:1px; line-height:1.2; color:var(--burg); margin:38px 0 16px;
                    display:flex; align-items:baseline; gap:10px; }}
  .titulo-bloque .cuenta {{ font-family:'Montserrat',sans-serif; font-size:12px; font-weight:700;
                            color:var(--gris); }}
  .rejilla {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(248px,1fr)); gap:20px; }}
  .ficha {{ background:#fff; border-radius:16px; overflow:hidden; box-shadow:var(--sombra);
            display:flex; flex-direction:column; transition:transform .22s ease, box-shadow .22s ease; }}
  .ficha:hover {{ transform:translateY(-5px); box-shadow:var(--sombra-alta); }}
  .ficha-foto {{ position:relative; display:block; aspect-ratio:4/3; background:var(--beige);
                 overflow:hidden; text-decoration:none; }}
  .ficha-foto img {{ width:100%; height:100%; object-fit:cover; display:block;
                     transition:transform .5s cubic-bezier(.2,.7,.3,1); }}
  .ficha:hover .ficha-foto img {{ transform:scale(1.05); }}
  .sin-foto {{ position:absolute; inset:0; display:grid; place-items:center; color:var(--burg);
               font-weight:800; letter-spacing:.08em; }}
  .marca-video {{ position:absolute; left:10px; bottom:10px; background:rgba(28,27,26,.72); color:#fff;
                  font-size:10.5px; font-weight:700; letter-spacing:.06em; padding:5px 9px;
                  border-radius:20px; backdrop-filter:blur(4px); }}
  .ficha-foto.exp {{ display:grid; place-content:center; text-align:center; gap:4px; color:#fff;
                     background-color:var(--burg-hondo); background-size:cover; background-position:center; }}
  .ficha-foto.exp::before {{ content:''; position:absolute; inset:0;
                     background:linear-gradient(180deg,rgba(0,0,0,.18) 0%,rgba(0,0,0,.05) 42%,rgba(0,0,0,.55) 100%); }}
  .ficha-foto.exp {{ place-content:end center; padding-bottom:14px; }}
  .ficha-foto.exp > * {{ position:relative; z-index:1;
                     text-shadow:0 2px 5px rgba(0,0,0,.7), 0 8px 26px rgba(0,0,0,.55); }}
  .ficha:hover .ficha-foto.exp::before {{ background:linear-gradient(180deg,rgba(0,0,0,.1) 0%,rgba(0,0,0,0) 42%,rgba(0,0,0,.48) 100%); }}
  .exp-rotulo {{ font-size:10.5px; letter-spacing:.2em; text-transform:uppercase; color:#fff;
                 font-weight:700; opacity:.95; }}
  .exp-destino {{ font-family:'Extenda','Montserrat',sans-serif; font-weight:400; font-size:30px;
                  line-height:1.2; letter-spacing:1px; padding:0 10px; }}
  .ficha-cuerpo {{ padding:13px 15px 15px; display:flex; flex-direction:column; gap:8px; flex:1; }}
  .kicker {{ font-size:10.5px; letter-spacing:.11em; text-transform:uppercase; color:var(--burg);
             font-weight:700; }}
  .ficha h3 {{ font-size:14.5px; line-height:1.32; font-weight:800; flex:1; }}
  .ficha h3 a {{ text-decoration:none; }}
  .ficha h3 a:hover {{ color:var(--burg); }}
  .acciones {{ display:flex; gap:8px; }}
  .btn-copiar {{ flex:1; background:var(--burg); color:#fff; border:0; border-radius:22px;
                 padding:10px 8px; font:inherit; font-size:12.5px; font-weight:700; cursor:pointer;
                 transition:filter .15s, background .2s; }}
  .btn-copiar:hover {{ filter:brightness(1.09); }}
  .btn-copiar.ok {{ background:#1C7C4A; }}
  .btn-copiar.falla {{ background:#8a6d1f; }}
  .btn-abrir {{ border:1.5px solid var(--linea); border-radius:22px; padding:9px 13px; font-size:12.5px;
                font-weight:700; text-decoration:none; color:var(--gris); }}
  .btn-abrir:hover {{ border-color:var(--burg); color:var(--burg); }}
  .nada {{ display:none; text-align:center; padding:56px 0; color:var(--gris); }}
  .nada strong {{ display:block; font-size:17px; color:var(--tinta); margin-bottom:5px; }}

  /* Footer del Figma (FooterWEB): cielo real del diseno + su escala rosada->burgundy.
     La foto de la chica vive quemada dentro de la imagen del Figma, no hay archivo suelto. */
  footer {{ margin-top:20px; color:#fff; text-align:center; border-radius:30px 30px 0 0;
            background:linear-gradient(180deg,rgba(228,19,70,0) 0,rgba(228,19,70,.55) 210px,#E41346 330px,#DF0B43 52%,#BD073B 78%,#A90635 100%),
                       url('assets/cielo-footer.webp') top center/cover no-repeat, #E41346;
            padding:74px 22px 26px; }}
  footer h2 {{ font-family:'Extenda','Montserrat',sans-serif; font-weight:400; line-height:1.14;
               font-size:clamp(28px,4.6vw,50px); letter-spacing:1px; max-width:760px; margin:0 auto;
               text-shadow:0 3px 22px rgba(0,0,0,.28); }}
  .pie-legal {{ max-width:1180px; margin:0 auto; border-top:1px solid rgba(255,255,255,.28);
                padding-top:16px; display:flex; flex-wrap:wrap; gap:6px 20px; justify-content:space-between;
                font-size:11.5px; opacity:.9; text-align:left; }}
  .pie-sede {{ font-size:12.5px; opacity:.95; margin:54px 0 14px; }}

  @media (max-width:760px) {{
    .hero-caja {{ grid-template-columns:1fr; padding-bottom:38px; }}
    .triana {{ display:none; }}
    main {{ padding-left:16px; padding-right:16px; }}
    /* 148px (no 158) para que quepan DOS columnas en un celular de 390px: con 158 se caia a una */
    .rejilla {{ grid-template-columns:repeat(auto-fill,minmax(148px,1fr)); gap:12px; }}
    .ficha-cuerpo {{ padding:11px 12px 13px; }}
    /* 44px de alto: el minimo comodo para el pulgar */
    .btn-copiar {{ min-height:44px; font-size:13px; }}
    .btn-abrir {{ min-height:44px; display:grid; place-items:center; }}
    .orden {{ margin-left:0; }}
  }}
  @media (prefers-reduced-motion:reduce) {{
    * {{ transition:none !important; animation:none !important; scroll-behavior:auto !important; }}
  }}
</style></head>
<body>

<header class="hero">
  <div class="hero-caja">
    <div>
      <img class="logo" src="{LOGO}" alt="Trvely">
      <p class="eyebrow">{total} galerías · {len(exps)} destinos de experiencias · {fotos:,} fotos</p>
      <h1>VITRINA</h1>
      <p class="firma">todo lo que puedes mostrar</p>
      <div class="buscar">
        <span class="lupa">🔍</span>
        <input id="q" type="search" placeholder="Busca un hotel o un destino…" autocomplete="off"
               aria-label="Buscar hotel, destino o experiencia">
      </div>
    </div>
    <picture>
      <source srcset="assets/triana.webp" type="image/webp">
      <img class="triana" src="assets/triana.png" alt="Triana, asesora Trvely" width="300">
    </picture>
  </div>
</header>

<div class="filtros" id="filtros">
  <div class="filtros-caja">
    <div class="chips" role="group" aria-label="Filtrar por destino">
{chr(10).join('      ' + c for c in chips)}
    </div>
    <div class="afinar">
      <label class="interruptor"><input type="checkbox" id="solo-video"> Solo con video</label>
      <label class="orden">Ordenar
        <select id="orden">
          <option value="az">A · Z</option>
          <option value="fotos">Más fotos primero</option>
        </select>
      </label>
    </div>
  </div>
</div>

<main>
{chr(10).join(secciones)}
  <p class="nada" id="nada"><strong>Sin resultados</strong>Prueba con otro nombre o quita los filtros.</p>
</main>

<footer>
  <h2>¡AQUÍ COMIENZAN TUS MÁS GRANDES AVENTURAS!</h2>
  <p class="pie-sede">Bogotá, Colombia</p>
  <div class="pie-legal">
    <span>Trvely S.A.S. · NIT: 901902687-9</span>
    <span>{total} galerías · {len(exps)} destinos de experiencias · actualizado {hoy}</span>
    <span>Copyright © 2026. Todos los derechos reservados.</span>
  </div>
</footer>

<script>
  var q = document.getElementById('q'), nada = document.getElementById('nada');
  var soloVideo = document.getElementById('solo-video'), selOrden = document.getElementById('orden');
  var chips = [].slice.call(document.querySelectorAll('.chip'));
  var destino = 'todos';

  function aplicar() {{
    var t = q.value.trim().toLowerCase(), video = soloVideo.checked, visibles = 0;
    document.querySelectorAll('.bloque').forEach(function (sec) {{
      var deSeccion = sec.dataset.seccion, vis = 0;
      sec.querySelectorAll('.ficha').forEach(function (f) {{
        var ok = (destino === 'todos' || destino === deSeccion)
              && (!t || f.dataset.buscar.indexOf(t) > -1)
              && (!video || f.dataset.video === '1');
        f.hidden = !ok;
        if (ok) vis++;
      }});
      sec.hidden = !vis;
      var c = sec.querySelector('.cuenta');
      if (c) c.textContent = vis;
      visibles += vis;
    }});
    nada.style.display = visibles ? 'none' : 'block';
  }}

  function ordenar() {{
    var porFotos = selOrden.value === 'fotos';
    document.querySelectorAll('.rejilla').forEach(function (r) {{
      [].slice.call(r.children)
        .sort(function (a, b) {{
          if (porFotos) return (+b.dataset.fotos) - (+a.dataset.fotos);
          return a.dataset.buscar.localeCompare(b.dataset.buscar, 'es');
        }})
        .forEach(function (f) {{ r.appendChild(f); }});
    }});
  }}

  chips.forEach(function (c) {{
    c.addEventListener('click', function () {{
      chips.forEach(function (o) {{ o.classList.remove('activo'); }});
      c.classList.add('activo');
      destino = c.dataset.filtroDestino;
      aplicar();
      window.scrollTo({{ top: document.querySelector('.filtros').offsetTop - 4, behavior: 'smooth' }});
    }});
  }});
  q.addEventListener('input', aplicar);
  soloVideo.addEventListener('change', aplicar);
  selOrden.addEventListener('change', function () {{ ordenar(); aplicar(); }});

  // Copiar con RESPALDO: si el navegador bloquea la API moderna (sin foco, permiso, contexto no
  // seguro), se usa el metodo viejo. El asesor SIEMPRE recibe respuesta: nunca un boton mudo.
  function porElMetodoViejo(txt) {{
    var ta = document.createElement('textarea');
    ta.value = txt; ta.setAttribute('readonly', '');
    ta.style.cssText = 'position:fixed;top:0;left:0;opacity:0';
    document.body.appendChild(ta); ta.select(); ta.setSelectionRange(0, txt.length);
    var ok = false;
    try {{ ok = document.execCommand('copy'); }} catch (e) {{ ok = false; }}
    document.body.removeChild(ta);
    return ok;
  }}
  function copiar(txt) {{
    if (navigator.clipboard && window.isSecureContext) {{
      return navigator.clipboard.writeText(txt).then(function () {{ return true; }},
                                                     function () {{ return porElMetodoViejo(txt); }});
    }}
    return Promise.resolve(porElMetodoViejo(txt));
  }}
  document.addEventListener('click', function (e) {{
    var b = e.target.closest('.btn-copiar');
    if (!b) return;
    var antes = b.dataset.antes || b.textContent;
    b.dataset.antes = antes;
    copiar(b.dataset.url).then(function (ok) {{
      b.textContent = ok ? '¡Copiado!' : 'Copia el enlace del título';
      b.classList.toggle('ok', ok); b.classList.toggle('falla', !ok);
      setTimeout(function () {{
        b.textContent = antes; b.classList.remove('ok', 'falla');
      }}, 1700);
    }});
  }});
</script>
</body></html>"""
    return pagina


def main():
    ruta = _opt("--json", os.path.join(AQUI, "vitrina.json"))
    with open(ruta, encoding="utf-8") as f:
        doc = json.load(f)
    if "verificacion" not in doc:
        sys.exit("ABORTA: el manifiesto no esta verificado. Corre antes gen_vitrina_verificar.py\n"
                 "  Publicar sin verificar es mandarle al asesor un enlace a ciegas.")
    pagina = construir_pagina(doc)

    salida = _opt("--salida", os.path.join(AQUI, "index.html"))
    repo = _opt("--publicar")
    if repo:
        salida = os.path.join(repo, "index.html")
        faltan = [a for a in ("assets/extenda.ttf", "assets/whitestar.otf", "assets/triana.webp",
                              "assets/triana.png", "assets/logo-beige.png", "assets/cielo-footer.webp")
                  if not os.path.isfile(os.path.join(repo, a))]
        if faltan:
            sys.exit("ABORTA: faltan assets en el repo -> " + ", ".join(faltan) +
                     "\n  Sin ellos la pagina se publica sin la tipografia de marca ni Triana.")
    with open(salida, "w", encoding="utf-8") as f:
        f.write(pagina)

    grupos = agrupar(doc)
    total = sum(len(v) for v in grupos.values())
    print("VITRINA - FASE 4 - la pagina (v2 PRO)\n")
    print(f"  {total} galerias en {len(grupos)} destinos + {len(doc.get('experiencias', []))} experiencias")
    print(f"  pagina -> {salida}  ({os.path.getsize(salida)/1024:.0f} KB)")


if __name__ == "__main__":
    main()

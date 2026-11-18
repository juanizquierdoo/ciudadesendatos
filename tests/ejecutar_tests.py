"""Comprobaciones automáticas de ciudadesendatos.

Uso (desde la carpeta del proyecto):   python tests/ejecutar_tests.py
No necesita instalar nada: solo usa la biblioteca estándar de Python.

Cada comprobación imprime OK, FALLA o PENDIENTE.
- FALLA: algo está mal y hay que arreglarlo.
- PENDIENTE: fallo conocido y anotado en BACKLOG.md; no rompe la ejecución,
  pero se sigue mostrando para no olvidarlo.
El programa termina con código 1 si hay algún FALLA (útil para automatizar).

Cómo añadir más comprobaciones: crea un archivo tests/test_<tema>.py que se
pueda ejecutar solo (python tests/test_<tema>.py), imprima lo que comprueba y
termine con sys.exit(1) si algo falla. Este script lo descubre y lo ejecuta al
final; no hace falta tocar este archivo.
"""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit, unquote
import json
import re
import subprocess
import sys

BASE = Path(__file__).resolve().parent.parent
WEB = BASE / "web"
JSON = BASE / "datos_limpios" / "ciudades_nivel1.json"

# Valores de referencia que SIEMPRE deben reproducirse (INSTRUCCIONES_PROYECTO.md)
REFERENCIA = {
    "28079": ("Madrid", 868.75, 53213, 19.6),
    "46250": ("Valencia", 680.83, 42374, 19.3),
    "47186": ("Valladolid", 530.83, 39685, 16.1),
}

# Fallos conocidos que todavía no se han arreglado (id de comprobación -> motivo)
PENDIENTES = {
    "titulo_largo": "B-05 en BACKLOG.md: acortar el título de las ciudades con nombre largo",
    "fecha_actualizacion": "B-01 en BACKLOG.md: el pie no indica la fecha de actualización que piden las licencias",
}

resultados = []


def comprobar(id_, descripcion, errores):
    errores = list(errores)
    if not errores:
        estado = "OK"
    elif id_ in PENDIENTES:
        estado = "PENDIENTE"
    else:
        estado = "FALLA"
    resultados.append(estado)
    print(f"[{estado:9}] {descripcion}")
    if estado == "PENDIENTE":
        print(f"            motivo: {PENDIENTES[id_]}")
    for e in errores[:8]:
        print("            -", e)
    if len(errores) > 8:
        print(f"            ... y {len(errores) - 8} más")


# ------------------------------------------------------------ lectura de páginas
VACIOS = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta",
          "source", "track", "wbr"}
OPCIONALES = {"li", "p", "td", "th", "tr", "dt", "dd", "option", "thead", "tbody"}


class Pagina(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.pila, self.errores = [], []
        self.ids, self.hrefs, self.srcs = [], [], []
        self.texto, self.title, self.desc, self.lang = [], None, None, None
        self._en, self._dentro_title = None, False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "html":
            self.lang = a.get("lang")
        if "id" in a:
            self.ids.append(a["id"])
        if tag == "a" and "href" in a:
            self.hrefs.append(a["href"])
        if tag in ("link", "script") and (a.get("href") or a.get("src")):
            self.srcs.append(a.get("href") or a.get("src"))
        if tag == "meta" and a.get("name") == "description":
            self.desc = a.get("content")
        if tag == "title" and self.title is None:   # solo el <title> del <head>, no los de los SVG
            self._dentro_title = True
            self.title = ""
        if tag in ("script", "style"):
            self._en = tag
        if tag not in VACIOS:
            self.pila.append((tag, self.getpos()[0]))

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in VACIOS:
            self.pila.pop()

    def handle_endtag(self, tag):
        if tag in ("script", "style"):
            self._en = None
        if tag == "title":
            self._dentro_title = False
        if tag in VACIOS:
            return
        # cierra etiquetas opcionales que se hayan quedado abiertas
        while self.pila and self.pila[-1][0] != tag and self.pila[-1][0] in OPCIONALES:
            self.pila.pop()
        if self.pila and self.pila[-1][0] == tag:
            self.pila.pop()
        else:
            self.errores.append(f"</{tag}> sin abrir (línea {self.getpos()[0]})")

    def handle_data(self, data):
        if self._dentro_title:
            self.title += data
        if self._en is None:
            self.texto.append(data)

    def cerrar(self):
        self.close()
        abiertas = [t for t, _ in self.pila if t not in OPCIONALES]
        if abiertas:
            self.errores.append("etiquetas sin cerrar: " + ", ".join(abiertas))


paginas = {}
for f in sorted(WEB.rglob("*.html")):
    p = Pagina()
    raw = f.read_text(encoding="utf-8")
    p.raw = raw
    p.feed(raw)
    p.cerrar()
    p.texto = re.sub(r"\s+", " ", " ".join(p.texto))
    paginas[f] = p

datos = json.loads(JSON.read_text(encoding="utf-8"))
ciudades = datos["ciudades"]
por_cod = {c["cod_muni"]: c for c in ciudades}

print(f"Páginas HTML encontradas: {len(paginas)} | ciudades en el JSON: {len(ciudades)}\n")

# ------------------------------------------------------------ 1. valores de referencia
err = []
for cod, (nom, alq, ren, pct) in REFERENCIA.items():
    c = por_cod.get(cod)
    if not c:
        err.append(f"{nom}: no está en el JSON")
        continue
    if abs(c["alquiler_mes"] - alq) > 0.005:
        err.append(f"{nom}: alquiler {c['alquiler_mes']} (esperado {alq})")
    if abs(c["renta_hogar"] - ren) > 0.5:
        err.append(f"{nom}: renta {c['renta_hogar']} (esperado {ren})")
    if abs(c["alquiler_pct_renta"] - pct) > 0.05:
        err.append(f"{nom}: alquiler/renta {c['alquiler_pct_renta']} (esperado {pct})")
comprobar("referencia_json", "Valores de referencia en ciudades_nivel1.json", err)

err = []
for cod, (nom, alq, ren, pct) in REFERENCIA.items():
    c = por_cod.get(cod)
    f = WEB / c["slug"] / "index.html" if c else None
    if not f or f not in paginas:
        err.append(f"{nom}: falta la página")
        continue
    t = paginas[f].texto
    esperados = [f"{round(alq):,}".replace(",", ".") + " €", f"{ren:,}".replace(",", ".") + " €",
                 f"{pct:.1f}".replace(".", ",") + " %"]
    for e in esperados:
        if e not in t:
            err.append(f"{nom}: no aparece «{e}» en la página")
comprobar("referencia_web", "Valores de referencia visibles en las páginas de Madrid, Valencia y Valladolid", err)

# ------------------------------------------------------------ 2. datos coherentes
err = []
pagina_slugs = {f.parent.name for f in paginas}
for c in ciudades:
    if c["slug"] not in pagina_slugs:
        err.append(f"{c['nombre']}: sin página")
    if (c.get("inmuebles") or 0) < 100:
        err.append(f"{c['nombre']}: se publica con {c.get('inmuebles')} inmuebles (mínimo 100)")
    if c.get("poblacion", 0) <= 50_000:
        err.append(f"{c['nombre']}: población {c.get('poblacion')} (debe superar 50.000)")
slugs = [c["slug"] for c in ciudades]
err += [f"slug repetido: {s}" for s in set(slugs) if slugs.count(s) > 1]
comprobar("datos", "Cada ciudad tiene página, más de 50.000 habitantes, 100+ inmuebles y slug único", err)

# distritos con menos de 30 inmuebles: el alquiler no debe verse
err = []
for c in ciudades:
    f = WEB / c["slug"] / "index.html"
    if f not in paginas:
        continue
    raw = paginas[f].raw
    for dd in c["distritos"]:
        if dd["fiabilidad"] in ("no_mostrar", "sin_dato"):
            fila = re.search(r'<tr><th scope="row" data-v="[^"]*">' + re.escape(dd["nombre"]) + r'</th>(.*?)</tr>', raw)
            if fila and re.search(r'<td data-v="\d', fila.group(1).split("</td>")[0]):
                err.append(f"{c['nombre']} / {dd['nombre']}: muestra alquiler con {dd['inmuebles']} inmuebles")
comprobar("fiabilidad", "Distritos con menos de 30 inmuebles no muestran el alquiler", err)

# ------------------------------------------------------------ 3. nada de nan/None visible
PROHIBIDO = re.compile(r"\b(nan|NaN|None|null|undefined|Infinity)\b")
err = []
for f, p in paginas.items():
    for m in PROHIBIDO.finditer(p.texto):
        err.append(f"{f.relative_to(WEB)}: «{m.group(0)}» en «…{p.texto[max(0, m.start()-40):m.end()+20]}…»")
    for atr in re.findall(r'(?:content|data-v|aria-label|title)="([^"]*)"', p.raw):
        if PROHIBIDO.search(atr):
            err.append(f"{f.relative_to(WEB)}: atributo con valor vacío «{atr[:60]}»")
comprobar("nan", "Ningún «nan», «None», «undefined»… visible en las páginas", err)

# ------------------------------------------------------------ 4. enlaces internos
err = []
for f, p in paginas.items():
    for h in p.hrefs + p.srcs:
        u = urlsplit(h)
        if u.scheme or h.startswith("//") or h.startswith("data:") or h.startswith("mailto:"):
            continue
        destino = f if not u.path else (f.parent / unquote(u.path)).resolve()
        if destino.is_dir():
            destino = destino / "index.html"
        if not destino.exists():
            err.append(f"{f.relative_to(WEB)} -> {h} (no existe)")
            continue
        if u.fragment and destino in paginas and u.fragment not in paginas[destino].ids:
            err.append(f"{f.relative_to(WEB)} -> {h} (no existe el ancla #{u.fragment})")
comprobar("enlaces", "Enlaces internos (páginas, anclas, CSS y JS) válidos", err)

# páginas huérfanas: alguna otra página debe enlazarlas
enlazadas = set()
for f, p in paginas.items():
    for h in p.hrefs:
        u = urlsplit(h)
        if not u.scheme and u.path:
            d = (f.parent / unquote(u.path)).resolve()
            enlazadas.add(d / "index.html" if d.is_dir() else d)
huerfanas = [str(f.relative_to(WEB)) for f in paginas if f not in enlazadas and f != WEB / "index.html"]
comprobar("huerfanas", "Ninguna página huérfana (sin enlaces desde otras)", huerfanas)

# ------------------------------------------------------------ 5. HTML bien formado y SEO básico
err = []
titulos, descs = {}, {}
for f, p in paginas.items():
    r = str(f.relative_to(WEB))
    if not p.raw.lower().startswith("<!doctype html>"):
        err.append(f"{r}: falta <!doctype html>")
    if p.lang != "es":
        err.append(f"{r}: falta lang=\"es\"")
    for e in p.errores:
        err.append(f"{r}: {e}")
    dup = {i for i in p.ids if p.ids.count(i) > 1}
    if dup:
        err.append(f"{r}: ids repetidos {sorted(dup)}")
    if not p.title:
        err.append(f"{r}: sin <title>")
    if not p.desc:
        err.append(f"{r}: sin meta description")
    if p.raw.count("<h1") != 1:
        err.append(f"{r}: {p.raw.count('<h1')} etiquetas <h1> (debe haber 1)")
    titulos.setdefault(p.title, []).append(r)
    descs.setdefault(p.desc, []).append(r)
comprobar("html", "HTML bien formado (doctype, lang, etiquetas cerradas, ids únicos, 1 h1, título y descripción)", err)

err = [f"{v[0]}: {len(k)} caracteres" for k, v in titulos.items() if k and len(k) > 70]
comprobar("titulo_largo", "Títulos de 70 caracteres o menos (Google corta los largos en los resultados)", err)

err = [f"título repetido en {len(v)} páginas: {k}" for k, v in titulos.items() if len(v) > 1]
err += [f"descripción repetida en {len(v)} páginas: {v[:3]}" for k, v in descs.items() if len(v) > 1]
comprobar("unicos", "Títulos y descripciones únicos por página", err)

# ------------------------------------------------------------ 6. fuente, licencia y fecha
err = []
for f, p in paginas.items():
    r = str(f.relative_to(WEB))
    t = p.texto
    if "Origen de los datos: Ministerio de Vivienda y Agenda Urbana" not in t:
        err.append(f"{r}: falta la cita del Ministerio de Vivienda")
    if "Elaboración propia con datos extraídos del sitio web del INE: www.ine.es" not in t:
        err.append(f"{r}: falta la cita del INE")
comprobar("fuente", "Cita literal de las fuentes (Ministerio de Vivienda e INE) en cada página", err)

err = []
FECHA = re.compile(r"(actualiza\w*|consulta\w*)[^.]{0,40}\b(\d{1,2}[/-]\d{1,2}[/-]\d{4}|\d{1,2} de \w+ de \d{4}|\w+ de \d{4})", re.I)
for f, p in paginas.items():
    if not FECHA.search(p.texto):
        err.append(f"{f.relative_to(WEB)}: no indica la fecha de actualización o consulta de los datos")
comprobar("fecha_actualizacion", "Fecha de actualización de los datos en cada página", err)

# ------------------------------------------------------------ otros tests (tests/test_*.py)
for t in sorted(Path(__file__).parent.glob("test_*.py")):
    print(f"\n--- {t.name} ---")
    r = subprocess.run([sys.executable, str(t)], cwd=BASE)
    comprobar(f"externo:{t.name}", f"{t.name} (código de salida {r.returncode})",
              [] if r.returncode == 0 else ["ver la salida de arriba"])

# ------------------------------------------------------------ resumen
print()
ok, fa, pe = resultados.count("OK"), resultados.count("FALLA"), resultados.count("PENDIENTE")
print(f"Resumen: {ok} OK, {fa} FALLA, {pe} PENDIENTE (de {len(resultados)} comprobaciones)")
sys.exit(1 if fa else 0)

"""Límites de municipios y distritos para el mapa de precios de España (/mapa/).

Fuente: cartografía de secciones censales del INE (contornos en SHAPE, ETRS89 UTM huso 30), licencia
CC BY 4.0 según su ficha de metadatos en idee.es (registro spaINE_SeccionesCensales). Se descarga de
https://www.ine.es/dyngs/DAB/index.htm?cid=1389 y el .zip se deja, sin descomprimir, en datos_originales/.

Qué hace (sin librerías externas, solo Python):
  1. Lee las secciones censales del .zip (formato SHAPE: .shp y .dbf).
  2. Une las secciones de cada municipio y de cada distrito: un lado que comparten dos secciones del
     mismo grupo es interior y se quita; lo que queda es el contorno del grupo.
  3. Simplifica los contornos para que pesen poco, sin abrir huecos entre vecinos: cada tramo de frontera
     entre dos vecinos se simplifica una sola vez y lo usan los dos (como TopoJSON).
  4. Escribe dos tipos de archivo en datos_limpios/mapa/:
       espana.json      todos los municipios, poco detalle (vista de toda España)
       p/<prov>.json    una provincia con más detalle: municipios y, donde hay más de uno, sus distritos
     Solo llevan geometría y códigos; los datos (alquiler, renta) los añade mapa_precios.py al generar la web,
     así que no hace falta repetir este paso cuando cambian los datos, solo cuando cambian los límites.

Canarias se dibuja desplazada junto a la península (recuadro), como en los mapas habituales.

Uso:  python preparar_mapa.py                       (usa el seccionado_AAAA.zip más reciente)
      python preparar_mapa.py datos_originales/seccionado_2024.zip
No forma parte de actualizar.py: solo hay que ejecutarlo cuando el INE cambia las secciones censales
y queremos los límites nuevos. Tarda unos minutos.
"""
import array
import io
import json
import math
import re
import struct
import sys
import zipfile
from collections import defaultdict
from pathlib import Path

BASE = Path(__file__).parent
ORIGEN = BASE / "datos_originales"
SALIDA = BASE / "datos_limpios" / "mapa"

# Resolución: unidad de las coordenadas guardadas (metros) y tolerancia de la simplificación (metros)
NAC_UNIDAD, NAC_TOL = 100, 450      # vista de toda España
PROV_UNIDAD, PROV_TOL = 10, 25      # vista de una provincia o una ciudad
CANARIAS = ("35", "38")


# ------------------------------------------------------------------ lectura del SHAPE
def leer_zip(ruta):
    z = zipfile.ZipFile(ruta)
    shps = sorted((i for i in z.infolist() if i.filename.lower().endswith(".shp")), key=lambda i: -i.file_size)
    if not shps:
        sys.exit(f"No hay ningún .shp dentro de {ruta}")
    shp = shps[0].filename
    base = shp[:-4]
    dbf = next(n for n in z.namelist() if n.lower() == (base + ".dbf").lower())
    prj = next((n for n in z.namelist() if n.lower() == (base + ".prj").lower()), None)
    return z.read(shp), z.read(dbf), (z.read(prj).decode("latin-1") if prj else ""), shp


def leer_dbf(b, campos):
    n, lcab, lreg = struct.unpack_from("<IHH", b, 4)
    defs, pos, off = {}, 32, 1
    while b[pos] != 0x0D:
        nombre = b[pos:pos + 11].split(b"\0")[0].decode("latin-1").upper()
        largo = b[pos + 16]
        defs[nombre] = (off, largo)
        off += largo
        pos += 32
    faltan = [c for c in campos if c not in defs]
    if faltan:
        sys.exit(f"Faltan columnas en el .dbf: {faltan}. Hay: {sorted(defs)}")
    filas = []
    for i in range(n):
        r = lcab + i * lreg
        filas.append({c: b[r + defs[c][0]:r + defs[c][0] + defs[c][1]].decode("latin-1").strip() for c in campos})
    return filas


def leer_shp(b):
    """Lista de polígonos; cada uno es una lista de anillos [x0, y0, x1, y1, ...] en metros."""
    out, pos, fin = [], 100, len(b)
    while pos + 8 <= fin:
        _, largo = struct.unpack_from(">ii", b, pos)
        pos += 8
        tipo = struct.unpack_from("<i", b, pos)[0]
        anillos = []
        if tipo in (5, 15, 25):
            npart, npt = struct.unpack_from("<ii", b, pos + 36)
            partes = list(struct.unpack_from(f"<{npart}i", b, pos + 44)) + [npt]
            p0 = pos + 44 + 4 * npart
            xy = array.array("d")
            xy.frombytes(b[p0:p0 + 16 * npt])
            if sys.byteorder == "big":
                xy.byteswap()
            for k in range(npart):
                anillos.append(xy[2 * partes[k]:2 * partes[k + 1]])
        out.append(anillos)
        pos += 2 * largo
    return out


# ------------------------------------------------------------------ unir secciones (disolver)
def cuantizar(anillo, u):
    """Coordenadas en enteros (unidad u metros), sin puntos repetidos seguidos ni cierre."""
    pts, ult = [], None
    for i in range(0, len(anillo), 2):
        p = (round(anillo[i] / u), round(anillo[i + 1] / u))
        if p != ult:
            pts.append(p)
            ult = p
    if len(pts) > 1 and pts[0] == pts[-1]:
        pts.pop()
    return pts


def disolver(anillos):
    """Contorno de la unión de varios anillos que encajan entre sí (lados comunes idénticos)."""
    lados = {}
    for pts in anillos:
        m = len(pts)
        if m < 3:
            continue
        for i in range(m):
            a, b = pts[i], pts[(i + 1) % m]
            if (b, a) in lados:
                lados[(b, a)] -= 1
                if not lados[(b, a)]:
                    del lados[(b, a)]
            else:
                lados[(a, b)] = lados.get((a, b), 0) + 1
    sig = defaultdict(list)
    for (a, b), k in lados.items():
        sig[a].extend([b] * k)
    out = []
    for inicio in list(sig):
        while sig.get(inicio):
            ring, p = [inicio], sig[inicio].pop()
            while p != inicio:
                ring.append(p)
                if not sig.get(p):
                    break
                p = sig[p].pop()
            if len(ring) >= 3:
                out.append(ring)
    return [r for r in (sin_pinchos(r) for r in out) if len(r) >= 3 and area(r) != 0]


def sin_pinchos(r):
    """Quita las idas y vueltas por el mismo punto (a, b, a -> a)."""
    st = []
    for p in r:
        if st and st[-1] == p:
            continue
        if len(st) >= 2 and st[-2] == p:
            st.pop()
            continue
        st.append(p)
    cambio = True
    while cambio and len(st) >= 3:
        cambio = False
        if st[0] == st[-1]:
            st.pop()
            cambio = True
        elif st[-2] == st[0]:
            st.pop()
            st.pop()
            cambio = True
        elif st[1] == st[-1]:
            st.pop(0)
            st.pop(0)
            cambio = True
    return st


def area(r):
    s = 0
    for i in range(len(r)):
        x1, y1 = r[i - 1]
        x2, y2 = r[i]
        s += x1 * y2 - x2 * y1
    return s / 2


# ------------------------------------------------------------------ topología y simplificación
def dp(pts, tol):
    """Douglas-Peucker con pila (sin recursión)."""
    n = len(pts)
    if n <= 2:
        return pts
    keep = [False] * n
    keep[0] = keep[-1] = True
    pila = [(0, n - 1)]
    t2 = tol * tol
    while pila:
        i, j = pila.pop()
        (x1, y1), (x2, y2) = pts[i], pts[j]
        dx, dy = x2 - x1, y2 - y1
        L = dx * dx + dy * dy
        mx, mk = -1, -1
        for k in range(i + 1, j):
            x, y = pts[k]
            if L == 0:
                d = (x - x1) ** 2 + (y - y1) ** 2
            else:
                c = (x - x1) * dy - (y - y1) * dx
                d = c * c / L
            if d > mx:
                mx, mk = d, k
        if mk > 0 and mx > t2:
            keep[mk] = True
            pila.append((i, mk))
            pila.append((mk, j))
    return [p for p, k in zip(pts, keep) if k]


def topologia(grupos, tol):
    """grupos: {id: [anillos]}. Devuelve (arcos, {id: [[referencias de arco]]}) estilo TopoJSON.

    Un punto es fijo si es de 3 o más grupos o si en algún anillo cambia el conjunto de grupos al pasar
    por él. Entre dos puntos fijos, el tramo es el mismo para los dos vecinos y se simplifica una vez."""
    dueños = defaultdict(set)
    for g, anillos in grupos.items():
        for r in anillos:
            for p in r:
                dueños[p].add(g)
    fijos = set()
    for anillos in grupos.values():
        for r in anillos:
            m = len(r)
            for i in range(m):
                d = dueños[r[i]]
                if len(d) >= 3 or d != dueños[r[i - 1]] or d != dueños[r[(i + 1) % m]]:
                    fijos.add(r[i])
    arcos, indice, geoms = [], {}, {}
    for g, anillos in grupos.items():
        out = []
        for r in anillos:
            pos = [i for i, p in enumerate(r) if p in fijos]
            if not pos:   # anillo sin vecinos con cambios (isla o enclave): un solo arco cerrado
                k = min(range(len(r)), key=lambda i: r[i])
                pos = [k]
            refs = []
            for a, b in zip(pos, pos[1:] + [pos[0] + len(r)]):
                tramo = [r[i % len(r)] for i in range(a, b + 1)]
                refs.append(arco(tramo, tol, arcos, indice))
            out.append(refs)
        geoms[g] = out
    return arcos, geoms


def arco(tramo, tol, arcos, indice):
    inv = tramo[::-1]
    if tramo[0] != tramo[-1]:
        al_reves = inv[0] < tramo[0]
    else:
        al_reves = len(tramo) > 2 and inv[1] < tramo[1]
    canon = tuple(inv if al_reves else tramo)
    if canon not in indice:
        s = dp(list(canon), tol)
        if canon[0] == canon[-1] and len(s) < 4:   # anillo cerrado demasiado pequeño: se guarda entero
            s = list(canon)
        indice[canon] = len(arcos)
        arcos.append(s)
    i = indice[canon]
    return ~i if al_reves else i


def delta(arcos, u_in, u_out):
    """Arcos en enteros de u_out metros con diferencias (como TopoJSON cuantizado)."""
    f = u_in / u_out
    out = []
    for a in arcos:
        px = py = 0
        r = []
        for x, y in a:
            qx, qy = round(x * f), round(y * f)
            if r and qx == px and qy == py:
                continue
            r.append([qx - px, qy - py])
            px, py = qx, qy
        if len(r) < 2:
            r.append([0, 0])
        out.append(r)
    return out


# ------------------------------------------------------------------ principal
def main():
    if len(sys.argv) > 1:
        ruta = Path(sys.argv[1])
    else:
        zips = sorted(ORIGEN.glob("seccionado_*.zip"))
        if not zips:
            sys.exit("Falta datos_originales/seccionado_AAAA.zip (cartografía de secciones censales del INE).")
        ruta = zips[-1]
    anio = re.search(r"(\d{4})", ruta.name).group(1)
    print(f"Leyendo {ruta.name} ...", flush=True)
    b_shp, b_dbf, prj, nombre = leer_zip(ruta)
    if prj and "30N" not in prj.replace(" ", "") and "zone_30" not in prj.lower() and "huso30" not in prj.lower().replace(" ", ""):
        print("AVISO: el .prj no dice UTM huso 30:", prj[:120])
    filas = leer_dbf(b_dbf, ["CUSEC", "CUMUN", "CUDIS", "CPRO"])
    polis = leer_shp(b_shp)
    if len(filas) != len(polis):
        sys.exit(f"El .dbf ({len(filas)}) y el .shp ({len(polis)}) no tienen las mismas filas")
    del b_shp
    print(f"  {len(polis)} secciones censales", flush=True)

    # Canarias: desplazamiento para dibujarla junto a la península
    def caja(cond):
        xs, ys = [], []
        for f, pol in zip(filas, polis):
            if cond(f["CPRO"]):
                for r in pol:
                    xs += [min(r[0::2]), max(r[0::2])]
                    ys += [min(r[1::2]), max(r[1::2])]
        return min(xs), min(ys), max(xs), max(ys)
    pen = caja(lambda p: p not in CANARIAS + ("51", "52", "07"))
    can = caja(lambda p: p in CANARIAS)
    # esquina inferior izquierda de la península, un poco por debajo
    dx = pen[0] + 60_000 - can[0]          # borde oeste de Canarias a 60 km del de la península
    dy = (pen[1] - 40_000) - can[3]         # borde norte de Canarias 40 km por debajo de la península
    marco = [can[0] + dx - 20_000, can[1] + dy - 20_000, can[2] + dx + 20_000, can[3] + dy + 20_000]

    def mover(f, r):
        if f["CPRO"] in CANARIAS:
            r = array.array("d", r)
            r[0::2] = array.array("d", (x + dx for x in r[0::2]))
            r[1::2] = array.array("d", (y + dy for y in r[1::2]))
        return r

    # 1) municipios y distritos a 1 metro, provincia a provincia
    por_muni = defaultdict(list)
    dist_de = defaultdict(set)
    for i, f in enumerate(filas):
        por_muni[f["CUMUN"]].append(i)
        dist_de[f["CUMUN"]].add(f["CUDIS"])
    prov_de = {m: filas[ix[0]]["CPRO"] for m, ix in por_muni.items()}
    munis = {}      # cod -> anillos (enteros de 1 m)
    distritos = {}  # cod distrito -> anillos (solo municipios con más de un distrito)
    for k, (m, ix) in enumerate(sorted(por_muni.items())):
        secc = {i: [cuantizar(mover(filas[i], r), 1) for r in polis[i]] for i in ix}
        munis[m] = disolver([r for i in ix for r in secc[i]])
        if len(dist_de[m]) > 1:
            por_d = defaultdict(list)
            for i in ix:
                por_d[filas[i]["CUDIS"]].extend(secc[i])
            for d, rs in por_d.items():
                distritos[d] = disolver(rs)
        if k % 1000 == 0:
            print(f"  municipios: {k}/{len(por_muni)}", flush=True)
    del polis
    print(f"  {len(munis)} municipios, {len(distritos)} distritos en municipios con más de uno", flush=True)

    SALIDA.mkdir(parents=True, exist_ok=True)
    (SALIDA / "p").mkdir(exist_ok=True)

    # 2) España: municipios con poco detalle
    nac = {m: [r2 for r2 in (recuant(r, NAC_UNIDAD) for r in rs) if r2] for m, rs in munis.items()}
    nac = {m: rs for m, rs in nac.items() if rs}
    sin = sorted(set(munis) - set(nac))
    for m in sin:   # municipio diminuto que desaparece a esta escala: se guarda como un cuadrado mínimo
        x, y = munis[m][0][0]
        cx, cy = round(x / NAC_UNIDAD), round(y / NAC_UNIDAD)
        nac[m] = [[(cx, cy), (cx + 1, cy), (cx + 1, cy + 1), (cx, cy + 1)]]
    arcos, geoms = topologia(nac, NAC_TOL / NAC_UNIDAD)
    # arcos de límite provincial (para dibujarlos más gruesos)
    lados = defaultdict(set)
    for m, rs in geoms.items():
        for refs in rs:
            for a in refs:
                lados[a if a >= 0 else ~a].add(prov_de[m])
    usados = defaultdict(int)
    for rs in geoms.values():
        for refs in rs:
            for a in refs:
                usados[a if a >= 0 else ~a] += 1
    limite_prov = sorted(i for i in range(len(arcos)) if len(lados[i]) > 1 or usados[i] == 1)
    cajas_prov = {}
    for m, rs in geoms.items():
        p = prov_de[m]
        for r in nac[m]:
            for x, y in r:
                c = cajas_prov.setdefault(p, [x, y, x, y])
                c[0], c[1], c[2], c[3] = min(c[0], x), min(c[1], y), max(c[2], x), max(c[3], y)
    esp = {"fuente": f"INE, cartografía de secciones censales ({anio})", "archivo": nombre, "unidad": NAC_UNIDAD,
           "canarias": [round(v / NAC_UNIDAD) for v in marco],
           "provincias": {p: c for p, c in sorted(cajas_prov.items())},
           "arcos": delta(arcos, 1, 1), "limites": limite_prov,
           "municipios": {m: geoms[m] for m in sorted(geoms)}}
    escribir(SALIDA / "espana.json", esp)

    # 3) provincias: municipios y distritos con más detalle
    for p in sorted(set(prov_de.values())):
        grupos = {}
        for m in sorted(x for x in munis if prov_de[x] == p):
            if len(dist_de[m]) > 1:
                for d in sorted(dist_de[m]):
                    rs = [r2 for r2 in (recuant(r, PROV_UNIDAD) for r in distritos[d]) if r2]
                    if rs:
                        grupos[d] = rs
            else:
                rs = [r2 for r2 in (recuant(r, PROV_UNIDAD) for r in munis[m]) if r2]
                if rs:
                    grupos[m] = rs
        arcos, geoms = topologia(grupos, PROV_TOL / PROV_UNIDAD)
        # arcos de límite municipal: los que separan dos municipios o dan al exterior
        lados, usados = defaultdict(set), defaultdict(int)
        for g, rs in geoms.items():
            for refs in rs:
                for a in refs:
                    lados[a if a >= 0 else ~a].add(g[:5])
                    usados[a if a >= 0 else ~a] += 1
        lim = sorted(i for i in range(len(arcos)) if len(lados[i]) > 1 or usados[i] == 1)
        escribir(SALIDA / "p" / f"{p}.json", {"unidad": PROV_UNIDAD, "arcos": delta(arcos, 1, 1), "limites": lim,
                                                "unidades": {g: geoms[g] for g in sorted(geoms)}})
    print(f"Listo: {SALIDA}")


def recuant(r, u):
    """Anillo de enteros de 1 m a enteros de u metros, sin repetidos ni pinchos; None si se queda en nada."""
    pts, ult = [], None
    for x, y in r:
        p = (round(x / u), round(y / u))
        if p != ult:
            pts.append(p)
            ult = p
    if len(pts) > 1 and pts[0] == pts[-1]:
        pts.pop()
    if len(pts) < 3:
        return None
    return pts if area(pts) != 0 else None


def escribir(ruta, obj):
    texto = json.dumps(obj, separators=(",", ":"))
    ruta.write_text(texto, encoding="utf-8")
    print(f"  {ruta.relative_to(BASE)}: {len(texto) / 1024:.0f} KB", flush=True)


if __name__ == "__main__":
    main()

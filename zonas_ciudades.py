"""Barrios con nombre de los distritos del INE en otras ciudades -> datos_limpios/zonas_nombradas.csv

Igual que zonas_valladolid.py, pero para ciudades cuyos datos municipales tienen otra forma.
Solo escribe las filas de sus municipios y conserva las demás (Valladolid y otras).
Nunca se inventa un nombre: todos salen de un fichero municipal guardado en datos_municipales/.
Solo se cambia la forma (MAYÚSCULAS -> mayúscula inicial).

Ciudades:
  * Sevilla (41091). Los 11 distritos municipales son los 11 distritos del INE: mismo orden y la
    población de cada uno coincide (padrón municipal 1-I-2024, Anuario Estadístico 2023 del Ayuntamiento,
    frente al ADRH 2024 del INE; el script lo comprueba). Barrios de cada distrito: capa "Barrios" de
    ide.SEVILLA (Gerencia de Urbanismo, CC BY 4.0).
  * Zaragoza (50297). Sus juntas municipales no son los distritos del INE. Se cruzaron las secciones
    censales del Ayuntamiento (capa ISV_Secciones_Censales_2024, con su población) con los límites de las
    juntas municipales y vecinales (IDEZar): cada sección va a la junta que contiene su centro. Resultado
    en datos_municipales/50297_zaragoza_juntas_por_distrito_censal.csv. Una junta se nombra si tiene al
    menos el 10 % de la población del distrito (y, en distritos de 10 secciones o más, al menos 2 secciones,
    para no fiarse de una sola sección rural grande).
  * Málaga (29067). Barrio de cada sección censal, cruzando las capas "Sección Censal" y "Barrio" del
    Ayuntamiento (datosabiertos.malaga.eu). Se pondera con la población del ADRH 2024 de cada sección y se
    nombran hasta 5 barrios con al menos el 5 % de la población del distrito (son muy pequeños). Los "diseminados" no cuentan.
    LICENCIA PENDIENTE: el portal dice CC BY 4.0 en el título y CC BY-SA 4.0 en la licencia del conjunto.
    No se escribe hasta que Juan lo decida (INCLUIR_MALAGA).
  * Las Palmas de Gran Canaria (35016). Capas "barrios" y "secciones" del SIT del Ayuntamiento
    (sit.laspalmasgc.es/server/rest/services/opendata). Las secciones municipales no dicen su distrito y su
    numeración se repite entre distritos, así que cada una se casa con la sección del INE (mismo número)
    cuyas calles (callejero electoral del INE, julio 2026) coinciden con las calles principales de la sección
    municipal. Si las calles no deciden, se usa el distrito de las secciones vecinas con los mismos barrios.
    Las que siguen dudosas o chocan con otra se descartan. Resultado y método fila a fila en
    datos_municipales/35016_laspalmas_barrio_por_seccion_censal.csv. Si una sección toca varios barrios, su
    población se reparte a partes iguales. Mismo umbral que Málaga (hasta 5 barrios con al menos el 5 %).

Uso: python zonas_ciudades.py   y después   python actualizar.py --desde 4
"""
import csv
import re
from collections import defaultdict

import pandas as pd

from config import ANIO, ARCHIVO_DEMOGRAFIA, DATOS

BASE = DATOS.parent / "datos_municipales"
SALIDA = DATOS / "zonas_nombradas.csv"
CACHE_POB = DATOS / f"poblacion_secciones_adrh_{ANIO}.csv"
MIN_CUOTA = 0.10
MIN_CUOTA_MALAGA, MAX_MALAGA = 0.05, 5   # en Málaga los barrios son muy pequeños (419 en la ciudad)
INCLUIR_MALAGA = True   # Juan aceptó la licencia CC BY-SA 4.0 para esta lista (20/11/2026)

MINUSCULAS = {"de", "del", "la", "las", "los", "el", "y", "i", "en"}
ROMANO = re.compile(r"^[IVXL]+$")

FUENTES = {
    "41091": ("Ayuntamiento de Sevilla, ide.SEVILLA (Gerencia de Urbanismo): capa 'Barrios' "
              "(services1.arcgis.com/hcmP7kr0Cx3AcTJk/.../Barrios_de_Sevilla), CC BY 4.0, actualizada el 12/06/2024, "
              "consultada el 20/11/2026. Distritos comprobados por población con el Anuario Estadístico de la ciudad de "
              "Sevilla 2023 (padrón municipal a 1/1/2024, Servicio de Estadística)",
              "Ayuntamiento de Sevilla, ide.SEVILLA (CC BY 4.0)"),
    "50297": ("Ayuntamiento de Zaragoza, IDEZar: capas 'Juntas municipales y vecinales' (urbanismo:Juntas_Municipales_Vecinales) "
              "e 'ISV Secciones Censales 2024' (ctsvg:ISV_Secciones_Censales_2024, con población por sección), consultadas el "
              "20/11/2026; reutilización comercial permitida según el Aviso legal de zaragoza.es (cita: 'Origen de los datos: "
              "Ayuntamiento de Zaragoza'). Cruce propio: cada sección censal se asigna a la junta que contiene su centro",
              "Origen de los datos: Ayuntamiento de Zaragoza (juntas municipales y vecinales)"),
    "29067": ("Ayuntamiento de Málaga, datosabiertos.malaga.eu: 'Sistema de Información Cartográfica - Barrio' y "
              "'- Sección Censal' (actualizados el 19/11/2026), consultados el 20/11/2026. Cruce propio: cada sección censal se "
              "asigna al barrio que contiene su centro; peso: población del ADRH 2024 del INE",
              "Ayuntamiento de Málaga, datos abiertos (CC BY-SA 4.0)"),
    "35016": ("Ayuntamiento de Las Palmas de Gran Canaria, SIT municipal (sit.laspalmasgc.es/server/rest/services/opendata): "
              "capas 'barrios' y 'secciones', consultadas el 20/11/2026; reutilización comercial y no comercial permitida según "
              "las Condiciones de reutilización de datosabiertos.laspalmasgc.es. Cruce propio con el callejero electoral del INE "
              "(julio 2026); peso: población del ADRH 2024 del INE",
              "Origen de los datos: Ayuntamiento de Las Palmas de Gran Canaria (barrios y secciones)"),
}


NOTAS = {
    "41091": "Los 11 distritos del Ayuntamiento son los del INE (mismo orden y misma población, con diferencias de entre "
             "el 1 y el 7 %); se indica el nombre del distrito municipal y todos los barrios que el Ayuntamiento sitúa en él.",
    "50297": "Las juntas municipales no coinciden con los distritos del INE: se nombran las juntas donde vive al menos el "
             "10 % de la población del distrito, según las secciones censales del Ayuntamiento (cruce propio).",
    "29067": "Los distritos del INE no son los distritos municipales: se nombran hasta 5 barrios donde vive al menos el 5 % "
             "de la población del distrito, según las secciones censales del Ayuntamiento (cruce propio). Esta lista de barrios "
             "se publica con licencia CC BY-SA 4.0, la de los datos de origen.",
    "35016": "Los distritos del INE no son los distritos municipales: se nombran hasta 5 barrios donde vive al menos el 5 % "
             "de la población del distrito. Cada sección censal del Ayuntamiento se ha situado en su distrito del INE "
             "comparando sus calles (cruce propio); unas pocas no se pudieron situar y no cuentan.",
}


def bonito(n):
    """Solo cambia mayúsculas: 'SAN PABLO D Y E' -> 'San Pablo D y E'; 'PIO XII' -> 'Pio XII'."""
    n = " ".join(n.split())
    if n != n.upper():
        return n
    out = []
    for i, pal in enumerate(n.split(" ")):
        partes = []
        for p in pal.split("-"):
            if ROMANO.match(p.rstrip(",")) and (p.rstrip(",") != "I" or i == len(n.split(" ")) - 1) and len(out) + len(partes) > 0:
                partes.append(p)
            elif "." in p or (len(p) == 1 and p.isalpha() and p not in ("Y", "I")):
                partes.append(p)
            elif i > 0 and "-" not in pal and p.lower() in MINUSCULAS:
                partes.append(p.lower())
            else:
                partes.append(p[:1].upper() + p[1:].lower())
        out.append("-".join(partes))
    return " ".join(out)


def normal(x):
    """Para comparar nombres sin tildes ni mayúsculas: 'Nervión' == 'NERVION'."""
    import unicodedata
    return "".join(c for c in unicodedata.normalize("NFD", x.lower()) if unicodedata.category(c) != "Mn")


def unicos(xs, clave=lambda x: x):
    vistos, res = set(), []
    for x in xs:
        if clave(x) not in vistos:
            vistos.add(clave(x))
            res.append(x)
    return res


def poblacion_ine_distritos(cod):
    d = pd.read_csv(DATOS / f"distritos_{ANIO}.csv", dtype=str)
    return d[d["cod_muni"] == cod]["codigo"].tolist()


def poblacion_secciones():
    """Población de cada sección censal (ADRH, año ANIO). Se guarda en caché la primera vez."""
    if not CACHE_POB.exists():
        print(f"Leyendo {ARCHIVO_DEMOGRAFIA.name} por trozos (solo la primera vez)...", flush=True)
        trozos = []
        for ch in pd.read_csv(ARCHIVO_DEMOGRAFIA, sep=";", dtype=str, chunksize=500_000):
            ch = ch[(ch["Periodo"] == str(ANIO)) & ch["Secciones"].notna() & (ch["Indicadores demográficos"] == "Población")]
            trozos.append(pd.DataFrame({"seccion": ch["Secciones"].str.split().str[0],
                                        "poblacion": ch["Total"].str.replace(".", "", regex=False)}))
        pd.concat(trozos).to_csv(CACHE_POB, index=False)
    p = pd.read_csv(CACHE_POB, dtype=str).dropna()
    return dict(zip(p["seccion"], p["poblacion"].astype(int)))


def poblacion_distritos_ine():
    """Población por distrito del ADRH (suma de sus secciones)."""
    tot = defaultdict(int)
    for s, v in poblacion_secciones().items():
        tot[s[:7]] += v
    return tot


def sevilla(pob_ine):
    cod = "41091"
    muni = pd.read_csv(BASE / "41091_sevilla_poblacion_distritos_2024.csv", sep=";", dtype=str)
    barrios = pd.read_csv(BASE / "41091_sevilla_barrios_por_distrito.csv", sep=";", dtype=str)
    filas = []
    ok = True
    for _, r in muni.iterrows():
        d = int(r["distrito"])
        p_mun, p_ine = int(r["poblacion_1_1_2024"]), pob_ine.get(f"{cod}{d:02d}", 0)
        dif = (p_ine - p_mun) / p_mun
        print(f"  Sevilla distrito {d:2} {r['nombre_distrito']:<22} Ayuntamiento {p_mun:>7} | INE {p_ine:>7} | {dif:+.1%}")
        if abs(dif) > 0.08:
            ok = False
    if not ok:
        print("  Sevilla: alguna población no cuadra (más del 8 %). No se escribe.")
        return []
    for d, g in barrios.groupby(barrios["distrito"].astype(int)):
        # Primero el nombre oficial del distrito (el más conocido: Triana, Macarena...) y luego sus barrios.
        distrito = g["nombre_distrito"].iloc[0].replace(" - ", "-")
        nombres = unicos([distrito] + [bonito(b) for b in g["barrio"]], clave=normal)
        filas.append((f"{cod}{d:02d}", nombres))
    return filas


def zaragoza():
    cod = "50297"
    t = pd.read_csv(BASE / "50297_zaragoza_juntas_por_distrito_censal.csv", sep=";", dtype={"distrito": str})
    filas = []
    for d, g in t.groupby("distrito"):
        total, nsec = g["poblacion"].sum(), g["secciones"].sum()
        g = g[~g["junta"].str.startswith("(")].sort_values("poblacion", ascending=False)
        sel = g[(g["poblacion"] / total >= MIN_CUOTA) & ((nsec < 10) | (g["secciones"] >= 2))]
        nombres = [bonito(j) for j in sel["junta"]]
        print(f"  Zaragoza distrito {d}: {', '.join(nombres)}")
        if nombres:
            filas.append((f"{cod}{d}", nombres))
    return filas


def malaga(pob_sec):
    cod = "29067"
    t = pd.read_csv(BASE / "29067_malaga_barrio_por_seccion_censal.csv", sep=";", dtype=str)
    t["pob"] = t["cusec"].map(pob_sec).fillna(0).astype(int)
    print(f"  Málaga: {int((t['pob'] == 0).sum())} secciones municipales sin población en el ADRH {ANIO} (no cuentan)")
    t["distrito"] = t["cusec"].str[:7]
    filas = []
    for d, g in t.groupby("distrito"):
        total = g["pob"].sum()
        g = g[~g["barrio"].str.match(r"^(DSMO|DISEMINADO)")]
        s = g.groupby("barrio")["pob"].sum().sort_values(ascending=False)
        nombres = [bonito(b) for b, v in s.items() if total and v / total >= MIN_CUOTA_MALAGA][:MAX_MALAGA]
        print(f"  Málaga distrito {d[-2:]}: {', '.join(nombres)}")
        if nombres:
            filas.append((d, nombres))
    return filas


def laspalmas(pob_sec):
    t = pd.read_csv(BASE / "35016_laspalmas_barrio_por_seccion_censal.csv", sep=";", dtype=str).fillna("")
    t = t[t["seccion_ine"] != ""].copy()
    t["pob"] = t["seccion_ine"].map(pob_sec).fillna(0).astype(float)
    tot = defaultdict(float)
    for s, p in pob_sec.items():
        if s.startswith("35016"):
            tot[s[:7]] += p
    reparto = defaultdict(lambda: defaultdict(float))
    for _, r in t.iterrows():
        bs = [b for b in r["barrios"].split("|") if not b.startswith("DISEMINADO")]
        for b in bs:
            reparto[r["seccion_ine"][:7]][b] += r["pob"] / len(bs)
    filas = []
    for d in sorted(reparto):
        cub = t.loc[t["seccion_ine"].str[:7] == d, "pob"].sum()
        s = sorted(reparto[d].items(), key=lambda x: -x[1])
        total = sum(v for _, v in s)
        nombres = [bonito(b) for b, v in s if total and v / total >= MIN_CUOTA_MALAGA][:MAX_MALAGA]
        print(f"  Las Palmas distrito {d[-2:]} (secciones situadas: {cub / tot[d]:.0%} de la población): {', '.join(nombres)}")
        if nombres:
            filas.append((d, nombres))
    return filas


def main():
    pob_sec = poblacion_secciones()
    pob_ine = poblacion_distritos_ine()
    filas = sevilla(pob_ine) + zaragoza() + laspalmas(pob_sec)
    m = malaga(pob_sec)
    if INCLUIR_MALAGA:
        filas += m
    else:
        print("  Málaga: calculado pero NO se escribe (licencia pendiente de decidir).")
    mios = set(FUENTES)
    otras = []
    if SALIDA.exists():
        otras = [r for r in csv.DictReader(open(SALIDA, encoding="utf-8")) if r["codigo"][:5] not in mios]
    nuevas = [{"codigo": c, "zonas": "|".join(n), "fuente": FUENTES[c[:5]][0], "cita": FUENTES[c[:5]][1],
               "nota": NOTAS[c[:5]]} for c, n in filas]
    with open(SALIDA, "w", encoding="utf-8", newline="") as out:
        w = csv.DictWriter(out, fieldnames=["codigo", "zonas", "fuente", "cita", "nota"], restval="")
        w.writeheader()
        w.writerows(otras + nuevas)
    print(f"Escritos {len(nuevas)} distritos ({', '.join(sorted({c[:5] for c, _ in filas}))}) en {SALIDA.name}; "
          f"conservadas {len(otras)} filas de otras ciudades")


if __name__ == "__main__":
    main()

from pathlib import Path
import json
import re
import unicodedata
from datetime import date

import numpy as np
import pandas as pd

from config import (ANIO, ANIO_INICIO_ALQUILER, ORIGEN, DATOS, MUNICIPIOS, DISTRITOS, RENTA_LARGO,
                    ARCHIVO_SERPAVI, JSON_NIVEL1, UMBRAL_POBLACION, REFERENCIA)

origen = ORIGEN
datos = DATOS

ANIOS = list(range(ANIO_INICIO_ALQUILER, ANIO + 1))
ARTICULOS = {"El", "La", "Los", "Las", "L'", "Les", "Els", "A", "O", "Os", "As", "Sa", "Ses", "Es"}


def nombre_bonito(nombre):
    """'Hospitalet de Llobregat, L'' -> 'L'Hospitalet de Llobregat'."""
    if not isinstance(nombre, str):
        return nombre
    if ", " in nombre:
        resto, art = nombre.rsplit(", ", 1)
        if art in ARTICULOS:
            return art + resto if art.endswith("'") else f"{art} {resto}"
    return nombre


def slug(texto):
    t = unicodedata.normalize("NFKD", texto)
    t = "".join(c for c in t if not unicodedata.combining(c)).lower()
    return re.sub(r"[^a-z0-9]+", "-", t).strip("-")


def limpio(v):
    if v is None:
        return None
    if isinstance(v, (np.integer,)):
        return int(v)
    if isinstance(v, (np.floating, float)):
        return None if np.isnan(v) else round(float(v), 2)
    return v


def leer_csv(ruta, **kw):
    for cod in ("utf-8-sig", "latin-1"):
        try:
            return pd.read_csv(ruta, encoding=cod, **kw)
        except UnicodeDecodeError:
            continue
    raise ValueError(f"No se pudo leer {ruta}")


# ---------- entradas ----------
mun = leer_csv(MUNICIPIOS, dtype={"cod_muni": str})
dis = leer_csv(DISTRITOS, dtype={"cod_muni": str, "codigo": str})
renta = leer_csv(RENTA_LARGO, dtype={"cod_muni": str, "codigo": str})

nombres = {}
citas = {}  # cita de la fuente de los nombres, por municipio (vacía si no está documentada, B-20)
f_nombres = datos / "nombres_distritos.csv"
if f_nombres.exists():
    nd = leer_csv(f_nombres, dtype=str)
    nombres = dict(zip(nd["codigo"].str.strip(), nd["nombre_distrito"].str.strip()))
    if "cita" in nd.columns:
        for cod_d, cita in zip(nd["codigo"].str.strip(), nd["cita"].fillna("").str.strip()):
            if cita:
                citas[cod_d[:5]] = cita
    print("Nombres de distrito cargados:", len(nombres))
else:
    print("AVISO: no existe nombres_distritos.csv; se usará 'Distrito N' en todas las ciudades.")

# Zonas de los distritos sin nombre oficial (preparar_zonas.py, callejero del INE)
zonas, fecha_callejero = {}, ""
f_zonas = datos / "zonas_distritos.csv"
if f_zonas.exists():
    zd = leer_csv(f_zonas, dtype=str).fillna("")
    for _, z in zd.iterrows():
        zonas[z["codigo"]] = {k: [x for x in z[k].split("|") if x] for k in ("cps", "calles", "nucleos")}
        fecha_callejero = z["fecha_callejero"]
    print("Zonas de distrito cargadas:", len(zonas))
else:
    print("AVISO: no existe zonas_distritos.csv; los distritos sin nombre se muestran como 'Distrito N'.")

# Barrios con nombre de los distritos sin nombre oficial (zonas_nombradas.csv: zonas del ayuntamiento
# que forman cada distrito, verificadas; lo escribe un script por ciudad, p. ej. zonas_valladolid.py)
barrios, citas_barrios = {}, {}
f_barrios = datos / "zonas_nombradas.csv"
if f_barrios.exists():
    zb = leer_csv(f_barrios, dtype=str).fillna("")
    for _, z in zb.iterrows():
        barrios[z["codigo"]] = [x for x in z["zonas"].split("|") if x]
        if z["cita"]:
            citas_barrios[z["codigo"][:5]] = z["cita"]
    print("Distritos con barrios con nombre:", len(barrios))


def lista_y(xs):
    return xs[0] if len(xs) == 1 else ", ".join(xs[:-1]) + " y " + xs[-1]


sel = mun[(mun["poblacion"] > UMBRAL_POBLACION) & (mun["fiabilidad"] == "ok")].copy()
print("Ciudades seleccionadas:", len(sel))

# ---------- series de alquiler (Excel del Ministerio) ----------
yy = [f"{a % 100:02d}" for a in ANIOS]
c_m2 = [f"ALQM2_LV_M_VC_{y}" for y in yy]
c_mes = [f"ALQTBID12_M_VC_{y}" for y in yy]
c_bi = [f"BI_ALVHEPCO_TVC_{y}" for y in yy]
ex = pd.read_excel(ARCHIVO_SERPAVI, sheet_name="Municipios",
                   usecols=["CUMUN"] + c_m2 + c_mes + c_bi)
ex["cod_muni"] = ex["CUMUN"].astype(int).astype(str).str.zfill(5)
ex = ex.drop_duplicates("cod_muni").set_index("cod_muni")

# ---------- serie de renta ----------
rm = renta[(renta["nivel"] == "municipio") & (renta["indicador"] == "renta_hogar")]
renta_serie = {c: g.sort_values("año") for c, g in rm.groupby("cod_muni")}

CAMPOS = ["poblacion", "edad_media", "pct_unipersonales", "pct_65_mas", "pct_espanola",
          "pct_menor_18", "tam_hogar", "renta_hogar", "renta_persona", "renta_mediana_uc",
          "alquiler_mes", "eur_m2", "eur_m2_p25", "eur_m2_p75", "superficie_m2",
          "inmuebles", "alquiler_pct_renta"]

ciudades = []
for _, f in sel.iterrows():
    cod = f["cod_muni"]
    serie_alq = []
    if cod in ex.index:
        for y, a in zip(yy, ANIOS):
            inm = ex.at[cod, f"BI_ALVHEPCO_TVC_{y}"]
            ok = pd.notna(inm) and inm >= 30
            serie_alq.append({
                "anio": a,
                "eur_m2": limpio(ex.at[cod, f"ALQM2_LV_M_VC_{y}"]) if ok else None,
                "alquiler_mes": limpio(ex.at[cod, f"ALQTBID12_M_VC_{y}"]) if ok else None,
                "inmuebles": limpio(inm),
            })
    serie_renta = []
    if cod in renta_serie:
        for _, r in renta_serie[cod].iterrows():
            serie_renta.append({"anio": int(r["año"]), "renta_hogar": limpio(r["valor"])})

    dd = dis[dis["cod_muni"] == cod].sort_values("codigo")
    distritos = []
    if len(dd) >= 2:
        for _, d in dd.iterrows():
            m = re.search(r"(\d+)\s*$", str(d["nombre_ine"]))
            num = int(m.group(1)) if m else None
            nombre_d = nombres.get(d["codigo"]) or (f"Distrito {num}" if num else d["nombre_ine"])
            zona = None
            bs = barrios.get(d["codigo"]) if d["codigo"] not in nombres else None
            if d["codigo"] not in nombres and d["codigo"] in zonas:
                # Sin nombre oficial: se identifica por sus códigos postales y calles (callejero del INE)
                zona = zonas[d["codigo"]]
            if bs:
                # ...o, mejor, por los barrios (zonas del ayuntamiento) que lo forman
                if len(bs) <= 3:
                    nombre_d += " · " + lista_y(bs)
                elif len(bs[0]) + len(bs[1]) <= 40:
                    nombre_d += f" · {bs[0]}, {bs[1]} y otros barrios"
                else:
                    nombre_d += f" · {bs[0]} y otros barrios"
            elif zona and zona["cps"]:
                nombre_d += " · CP " + " y ".join(zona["cps"][:2])
            distritos.append({
                "codigo": d["codigo"], "numero": num, "nombre": nombre_d,
                "con_nombre_oficial": d["codigo"] in nombres, "zona": zona, "barrios": bs or [],
                **{k: limpio(d.get(k)) for k in ["renta_hogar", "renta_persona", "eur_m2",
                                                  "alquiler_mes", "superficie_m2", "inmuebles",
                                                  "alquiler_pct_renta", "fiabilidad"]},
            })

    nombre = nombre_bonito(f["nombre_muni"])
    ciudades.append({
        "cod_muni": cod, "nombre": nombre, "slug": slug(nombre),
        "provincia": nombre_bonito(f["provincia"]),
        **{k: limpio(f.get(k)) for k in CAMPOS},
        "serie_alquiler": serie_alq, "serie_renta": serie_renta, "distritos": distritos,
        "cita_nombres_distritos": citas.get(cod, "") if any(x["con_nombre_oficial"] for x in distritos) else "",
        "cita_barrios": citas_barrios.get(cod, "") if any(x["barrios"] for x in distritos) else "",
    })

# slugs repetidos: añadir la provincia
vistos = {}
for c in ciudades:
    vistos.setdefault(c["slug"], []).append(c)
for s, lista in vistos.items():
    if len(lista) > 1:
        for c in lista:
            c["slug"] = f"{s}-{slug(c['provincia'])}"
        print("Slug repetido resuelto:", s, "->", [c["slug"] for c in lista])

salida = {"generado": date.today().isoformat(), "anio_datos": ANIO, "fecha_callejero": fecha_callejero, "ciudades": ciudades}
ruta_json = JSON_NIVEL1
ruta_json.write_text(json.dumps(salida, ensure_ascii=False, indent=1), encoding="utf-8")
print(f"\nGuardado {ruta_json.name}: {round(ruta_json.stat().st_size / 1024)} KB")

# ---------- comprobaciones ----------
print("\n=== COMPROBACIÓN CON LAS TRES CIUDADES DE PRUEBA ===")
esperado = REFERENCIA.get(ANIO, {})
if not esperado:
    print(f"AVISO: no hay valores de referencia para {ANIO} en config.py")
por_cod = {c["cod_muni"]: c for c in ciudades}
fallos = 0
for cod, (_, alq, ren, pct) in esperado.items():
    c = por_cod.get(cod)
    if not c:
        print(cod, "NO ESTÁ EN LA LISTA")
        fallos += 1
        continue
    ok = abs(c["alquiler_mes"] - alq) < 0.5 and abs(c["renta_hogar"] - ren) < 1 and abs(c["alquiler_pct_renta"] - pct) < 0.1
    print(f"{c['nombre']:<12} alquiler {c['alquiler_mes']} | renta {c['renta_hogar']} | "
          f"{c['alquiler_pct_renta']} % | distritos {len(c['distritos'])} -> {'OK' if ok else 'REVISAR'}")
    fallos += 0 if ok else 1

completas = sum(1 for c in ciudades if sum(1 for s in c["serie_alquiler"] if s["eur_m2"] is not None) == len(ANIOS))
print(f"\nCiudades con serie de alquiler completa {ANIOS[0]}-{ANIOS[-1]}:", completas, "de", len(ciudades))
print("Ciudades con desglose por distrito:", sum(1 for c in ciudades if c["distritos"]))
print("Distritos en total:", sum(len(c["distritos"]) for c in ciudades))
print("Distritos con nombre oficial:", sum(1 for c in ciudades for d in c["distritos"] if d["con_nombre_oficial"]))

if fallos:
    import sys
    print(f"\nERROR: {fallos} ciudad(es) de referencia no cuadran. Revisa antes de generar la web.")
    sys.exit(1)

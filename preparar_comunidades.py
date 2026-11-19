"""Alquiler oficial por comunidad autónoma (SERPAVI) para las páginas de comunidades (B-18).

Uso:  python preparar_comunidades.py
Lee las hojas "CCAA" y "Provincias" del fichero SERPAVI y escribe datos_limpios/comunidades.json.

La relación provincia -> comunidad usa los códigos del INE (los mismos que trae el SERPAVI).
Se comprueba contra el propio fichero: para cada comunidad y cada año, la suma de inmuebles de
sus provincias debe ser igual al total de la comunidad. Si no cuadra, el script termina con error.
"""
import json
import math
import sys

import pandas as pd

from config import ANIO, ANIO_INICIO_ALQUILER, ARCHIVO_SERPAVI, DATOS, yy

SALIDA = DATOS / "comunidades.json"

# Código INE de comunidad -> códigos INE de sus provincias
CCAA_PROVINCIAS = {
    "01": ["04", "11", "14", "18", "21", "23", "29", "41"],   # Andalucía
    "02": ["22", "44", "50"],                                 # Aragón
    "03": ["33"],                                             # Principado de Asturias
    "04": ["07"],                                             # Illes Balears
    "05": ["35", "38"],                                       # Canarias
    "06": ["39"],                                             # Cantabria
    "07": ["05", "09", "24", "34", "37", "40", "42", "47", "49"],  # Castilla y León
    "08": ["02", "13", "16", "19", "45"],                     # Castilla-La Mancha
    "09": ["08", "17", "25", "43"],                           # Cataluña
    "10": ["03", "12", "46"],                                 # Comunitat Valenciana
    "11": ["06", "10"],                                       # Extremadura
    "12": ["15", "27", "32", "36"],                           # Galicia
    "13": ["28"],                                             # Comunidad de Madrid
    "14": ["30"],                                             # Región de Murcia
    "15": ["31"],                                             # Comunidad Foral de Navarra
    "16": ["01", "20", "48"],                                 # País Vasco
    "17": ["26"],                                             # La Rioja
    "18": ["51"],                                             # Ceuta
    "19": ["52"],                                             # Melilla
}
UMBRAL_INMUEBLES = 100   # igual que en las ciudades


def num(v):
    return None if v is None or (isinstance(v, float) and math.isnan(v)) else float(v)


def main():
    hojas = pd.read_excel(ARCHIVO_SERPAVI, sheet_name=["CCAA", "Provincias"], dtype={"CCAA": str, "CPRO": str})
    cc = hojas["CCAA"].dropna(subset=["CCAA"]).copy()
    pr = hojas["Provincias"].dropna(subset=["CPRO"]).copy()
    cc["CCAA"] = cc["CCAA"].astype(str).str.replace(r"\.0$", "", regex=True).str.zfill(2)
    pr["CPRO"] = pr["CPRO"].astype(str).str.replace(r"\.0$", "", regex=True).str.zfill(2)
    cc, pr = cc.set_index("CCAA"), pr.set_index("CPRO")

    # comprobación de la relación provincia -> comunidad con el propio fichero
    errores = []
    if sorted(cc.index) != sorted(CCAA_PROVINCIAS):
        errores.append(f"comunidades distintas: {sorted(cc.index)}")
    if sorted(p for ps in CCAA_PROVINCIAS.values() for p in ps) != sorted(pr.index):
        errores.append("las provincias de la tabla no son las 52 del fichero")
    comprobadas = 0
    for a in range(ANIO_INICIO_ALQUILER, ANIO + 1):
        col = f"BI_ALVHEPCO_TVC_{yy(a)}"
        for cod, provs in CCAA_PROVINCIAS.items():
            tot = num(cc.at[cod, col])
            if tot is None:
                continue
            suma = sum(num(pr.at[p, col]) or 0 for p in provs)
            comprobadas += 1
            if abs(suma - tot) > 0.5:
                errores.append(f"{cc.at[cod, 'LITCCAA']} {a}: provincias {suma:.0f} frente a comunidad {tot:.0f}")
    if errores:
        print("ERROR: la relación provincia -> comunidad no cuadra con el SERPAVI:")
        for e in errores:
            print("  -", e)
        sys.exit(1)

    y = yy(ANIO)
    salida = []
    for cod, provs in CCAA_PROVINCIAS.items():
        f = cc.loc[cod]
        inm = num(f[f"BI_ALVHEPCO_TVC_{y}"])
        fiable = inm is not None and inm >= UMBRAL_INMUEBLES
        serie = []
        for a in range(ANIO_INICIO_ALQUILER, ANIO + 1):
            v = num(f[f"ALQM2_LV_M_VC_{yy(a)}"])
            n_a = num(f[f"BI_ALVHEPCO_TVC_{yy(a)}"])
            if v is not None and n_a is not None and n_a >= UMBRAL_INMUEBLES:
                serie.append({"anio": a, "eur_m2": round(v, 2)})
        salida.append({
            "cod_ccaa": cod,
            "nombre": str(f["LITCCAA"]).strip(),
            "provincias": provs,
            "inmuebles": inm,
            "alquiler_mes": round(num(f[f"ALQTBID12_M_VC_{y}"]), 2) if fiable else None,
            "eur_m2": round(num(f[f"ALQM2_LV_M_VC_{y}"]), 2) if fiable else None,
            "eur_m2_p25": round(num(f[f"ALQM2_LV_25_VC_{y}"]), 2) if fiable else None,
            "eur_m2_p75": round(num(f[f"ALQM2_LV_75_VC_{y}"]), 2) if fiable else None,
            "superficie_m2": num(f[f"SLVM2_M_VC_{y}"]) if fiable else None,
            "serie_alquiler": serie,
        })
    SALIDA.write_text(json.dumps({"anio_datos": ANIO, "fuente": "SERPAVI, hoja CCAA (vivienda colectiva)",
                                  "comunidades": salida}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"Comunidades: {len(salida)} | relación provincia -> comunidad comprobada en {comprobadas} pares comunidad-año")
    for c in salida:
        print(f"  {c['cod_ccaa']} {c['nombre']:<28} {c['alquiler_mes']} €/mes  {c['eur_m2']} €/m²  serie {len(c['serie_alquiler'])} años")
    print(f"Escrito: {SALIDA}")


if __name__ == "__main__":
    main()

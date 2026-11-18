from pathlib import Path
import re
import numpy as np
import pandas as pd

from config import ANIO, ORIGEN, DATOS, DEMOGRAFIA, RENTA_LARGO

origen = ORIGEN
destino = DATOS
destino.mkdir(exist_ok=True)

PATRON = re.compile(r"-?\d{1,3}(\.\d{3})*(,\d+)?|-?\d+(,\d+)?")

def num(s):
    """'17.411' -> 17411.0 ; '40,8' -> 40.8 ; marcadores ('.', '..') -> NaN."""
    s = str(s).strip()
    if PATRON.fullmatch(s):
        return float(s.replace(".", "").replace(",", "."))
    return np.nan

def leer(nombre):
    return pd.read_csv(origen / nombre, sep=";", encoding="utf-8",
                       encoding_errors="replace", dtype=str, chunksize=500_000)

def preparar(t, col_indicador):
    t = t.copy()
    m = t["Municipios"].str.extract(r"^(\d+)\s+(.*)$")
    d = t["Distritos"].str.extract(r"^(\d+)\s+(.*)$")
    es_dist = t["Distritos"].notna()
    t["cod_muni"] = m[0]
    t["nombre_muni"] = m[1]
    t["nivel"] = np.where(es_dist, "distrito", "municipio")
    t["codigo"] = np.where(es_dist, d[0], m[0])
    t["nombre"] = np.where(es_dist, d[1], m[1])
    t["indicador"] = t[col_indicador]
    t["año"] = t["Periodo"].astype(int)
    t["valor"] = t["Total"].map(num)
    return t[["cod_muni", "nombre_muni", "nivel", "codigo", "nombre",
              "indicador", "año", "valor"]]

# ---------- 1) RENTA: municipios y distritos ----------
INDICADORES = {
    "Renta neta media por hogar": "renta_hogar",
    "Renta neta media por persona": "renta_persona",
    "Mediana de la renta por unidad de consumo": "renta_mediana_uc",
}
trozos = []
vistos = set()
for t in leer("renta_total.csv"):
    vistos.update(t["Indicadores de renta media"].dropna().unique())
    t = t[t["Secciones"].isna() & t["Indicadores de renta media"].isin(INDICADORES)]
    trozos.append(preparar(t, "Indicadores de renta media"))
renta = pd.concat(trozos, ignore_index=True)
renta["indicador"] = renta["indicador"].map(INDICADORES)
renta.to_csv(RENTA_LARGO, index=False, encoding="utf-8-sig")
print("Indicadores de renta que trae el archivo:", sorted(vistos))
print("Renta guardada:", len(renta), "filas")

# ---------- 2) DEMOGRAFÍA: solo municipios, año ANIO ----------
trozos = []
for t in leer("demograficos_total.csv"):
    t = t[t["Secciones"].isna() & t["Distritos"].isna() & (t["Periodo"] == str(ANIO))]
    trozos.append(preparar(t, "Indicadores demográficos"))
demo = pd.concat(trozos, ignore_index=True)
demo.to_csv(DEMOGRAFIA, index=False, encoding="utf-8-sig")

indicadores = sorted(demo["indicador"].unique())
print("\nIndicadores demográficos:")
for i in indicadores:
    print(" -", i)

# ---------- 3) RESUMEN ----------
pob_ind = next((i for i in indicadores if i.lower().startswith("población")), None)
print("\nIndicador usado como población:", pob_ind)

if pob_ind:
    pob = demo[demo["indicador"] == pob_ind].set_index("cod_muni")
    print("\nMunicipios por tamaño:")
    for umbral in (100_000, 50_000, 20_000, 10_000, 5_000):
        print(f"  más de {umbral:>7,}: {(pob['valor'] > umbral).sum()}".replace(",", "."))
    print("\nLos 10 mayores:")
    print(pob.sort_values("valor", ascending=False)[["nombre_muni", "valor"]].head(10).to_string())

    r = renta[(renta["año"] == ANIO) & (renta["indicador"] == "renta_hogar")]
    n_dist = r[r["nivel"] == "distrito"].groupby("cod_muni").size()
    con_varios = n_dist[n_dist >= 2]
    print("\nMunicipios con 2 o más distritos:", len(con_varios))
    grandes = set(pob[pob["valor"] > 50_000].index)
    print("De ellos, con más de 50.000 habitantes:", len(grandes & set(con_varios.index)))
    print("Municipios de más de 50.000 habitantes con un único distrito:",
          len(grandes - set(con_varios.index)))
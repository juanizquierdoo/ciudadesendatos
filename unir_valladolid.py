from pathlib import Path
import numpy as np
import pandas as pd

pd.set_option("display.width", 250)
pd.set_option("display.max_columns", 30)

carpeta = Path(__file__).parent / "datos_originales"

def num(s):
    """Convierte '17.411' en 17411.0 y '.' en NaN (formato INE)."""
    s = str(s).strip()
    if s in (".", "", "nan"):
        return np.nan
    return float(s.replace(".", "").replace(",", "."))

# ---------- 1) RENTA (INE, formato largo) ----------
renta = pd.read_csv(carpeta / "renta_valladolid.csv", sep=";", encoding="utf-8", dtype=str)
renta["valor"] = renta["Total"].map(num)
renta["año"] = renta["Periodo"].astype(int)

renta["territorio"] = renta["Secciones"].fillna(renta["Distritos"]).fillna(renta["Municipios"])
renta["nivel"] = np.where(renta["Secciones"].notna(), "seccion",
                  np.where(renta["Distritos"].notna(), "distrito", "municipio"))
renta["codigo"] = renta["territorio"].str.split(" ", n=1).str[0]
renta["nombre"] = renta["territorio"].str.split(" ", n=1).str[1]

print("Territorios por nivel (esperado 225 / 245 / 580):")
print((renta.groupby("nivel").size() / 60).astype(int))

# Valladolid ciudad, año 2024, renta neta media por hogar
vall = renta[(renta["codigo"].str.startswith("47186")) & (renta["año"] == 2024)]
ind = "Renta neta media por hogar"
r = vall[vall["Indicadores de renta media y mediana"] == ind]
r = r[r["nivel"].isin(["municipio", "distrito"])][["nivel", "codigo", "nombre", "valor"]]
r = r.rename(columns={"valor": "renta_hogar"})
print("\n=== RENTA NETA MEDIA POR HOGAR 2024, Valladolid ===")
print(r.to_string(index=False))

# ---------- 2) ALQUILER (SERPAVI) ----------
ruta = carpeta / "Datos_municipios_2024.xlsx"
cols = ["BI_ALVHEPCO_TVC_24", "ALQM2_LV_M_VC_24", "ALQTBID12_M_VC_24"]

dist = pd.read_excel(ruta, sheet_name="Distritos")
dist = dist[dist["CUMUN"] == 47186][["CUDIS"] + cols]
dist["codigo"] = dist["CUDIS"].astype(str)

muni = pd.read_excel(ruta, sheet_name="Municipios")
muni = muni[muni["CUMUN"] == 47186][["CUMUN"] + cols]
muni["codigo"] = muni["CUMUN"].astype(str)

alq = pd.concat([dist.drop(columns="CUDIS"), muni.drop(columns="CUMUN")])
alq = alq.rename(columns={"BI_ALVHEPCO_TVC_24": "inmuebles",
                          "ALQM2_LV_M_VC_24": "eur_m2",
                          "ALQTBID12_M_VC_24": "alquiler_mes"})

# ---------- 3) UNIÓN ----------
union = r.merge(alq, on="codigo", how="outer", indicator=True)
print("\n¿Coinciden los códigos? (both = unión correcta)")
print(union["_merge"].value_counts())

union["alquiler_pct_renta"] = (union["alquiler_mes"] * 12 / union["renta_hogar"] * 100).round(1)
print("\n=== UNIÓN RENTA + ALQUILER, Valladolid 2024 ===")
print(union.drop(columns="_merge").round(2).to_string(index=False))
from pathlib import Path
import numpy as np
import pandas as pd

pd.set_option("display.width", 250)
pd.set_option("display.max_columns", 30)

base = Path(__file__).parent
origen = base / "datos_originales"
datos = base / "datos_limpios"

# ---------- 1) RENTA 2024 (municipios y distritos) ----------
renta = pd.read_csv(datos / "renta_nacional_largo.csv", encoding="utf-8-sig",
                    dtype={"cod_muni": str, "codigo": str})
r24 = renta[renta["año"] == 2024]
ren = (r24.pivot_table(index=["nivel", "codigo", "cod_muni", "nombre"],
                       columns="indicador", values="valor")
          .reset_index())
ren.columns.name = None

# ---------- 2) DEMOGRAFÍA 2024 (municipios) ----------
demo = pd.read_csv(datos / "demografia_municipios_2024.csv", encoding="utf-8-sig",
                   dtype={"cod_muni": str})
dem = (demo.pivot_table(index=["cod_muni", "nombre_muni"], columns="indicador", values="valor")
           .reset_index())
dem.columns.name = None
dem = dem.rename(columns={
    "Población": "poblacion",
    "Edad media de la población": "edad_media",
    "Porcentaje de hogares unipersonales": "pct_unipersonales",
    "Porcentaje de población de 65 y más años": "pct_65_mas",
    "Porcentaje de población española": "pct_espanola",
    "Porcentaje de población menor de 18 años": "pct_menor_18",
    "Tamaño medio del hogar": "tam_hogar",
})

# ---------- 3) ALQUILER SERPAVI 2024 ----------
cols = {
    "BI_ALVHEPCO_TVC_24": "inmuebles",
    "ALQM2_LV_M_VC_24": "eur_m2",
    "ALQM2_LV_25_VC_24": "eur_m2_p25",
    "ALQM2_LV_75_VC_24": "eur_m2_p75",
    "ALQTBID12_M_VC_24": "alquiler_mes",
    "SLVM2_M_VC_24": "superficie_m2",
}
ruta = origen / "Datos_municipios_2024.xlsx"

am = pd.read_excel(ruta, sheet_name="Municipios",
                   usecols=["NPRO", "CUMUN"] + list(cols))
am["cod_muni"] = am["CUMUN"].astype(int).astype(str).str.zfill(5)   # 1001 -> 01001
am = am.rename(columns={"NPRO": "provincia", **cols}).drop(columns="CUMUN")

ad = pd.read_excel(ruta, sheet_name="Distritos", usecols=["CUDIS"] + list(cols))
ad["codigo"] = ad["CUDIS"].astype(int).astype(str).str.zfill(7)     # 100101 -> 0100101
ad = ad.rename(columns=cols).drop(columns="CUDIS")

def fiabilidad(n):
    if pd.isna(n):
        return "sin_dato"
    if n >= 100:
        return "ok"
    if n >= 30:
        return "pocos_datos"
    return "no_mostrar"

# ---------- 4) UNIÓN ----------
rm = ren[ren["nivel"] == "municipio"].drop(columns=["nivel", "nombre", "codigo"])
m = dem.merge(rm, on="cod_muni", how="left").merge(am, on="cod_muni", how="left")
m["alquiler_pct_renta"] = (m["alquiler_mes"] * 12 / m["renta_hogar"] * 100).round(1)
m["fiabilidad"] = m["inmuebles"].map(fiabilidad)
m["anio"] = 2024
m = m.sort_values("poblacion", ascending=False).reset_index(drop=True)

rd = ren[ren["nivel"] == "distrito"].drop(columns=["nivel"]).rename(columns={"nombre": "nombre_ine"})
dd = (rd.merge(ad, on="codigo", how="left")
        .merge(dem[["cod_muni", "nombre_muni", "poblacion"]], on="cod_muni", how="left"))
dd["alquiler_pct_renta"] = (dd["alquiler_mes"] * 12 / dd["renta_hogar"] * 100).round(1)
dd["fiabilidad"] = dd["inmuebles"].map(fiabilidad)
dd["anio"] = 2024

m.to_csv(datos / "municipios_2024.csv", index=False, encoding="utf-8-sig")
dd.to_csv(datos / "distritos_2024.csv", index=False, encoding="utf-8-sig")
print("Guardados: municipios_2024.csv (%d filas) y distritos_2024.csv (%d filas)" % (len(m), len(dd)))

# ---------- 5) INFORME ----------
print("\nMunicipios sin renta 2024:", m["renta_hogar"].isna().sum(),
      "| sin fila de alquiler:", m["inmuebles"].isna().sum() + 0)

g = m[m["poblacion"] > 50_000]
print("\n=== CIUDADES DE MÁS DE 50.000 HABITANTES:", len(g), "===")
print("Fiabilidad del alquiler municipal (pisos):")
print(g["fiabilidad"].value_counts().to_string())

malas = g[g["fiabilidad"] != "ok"]
if len(malas):
    print("\nCiudades grandes SIN dato de alquiler fiable:")
    print(malas[["nombre_muni", "provincia", "poblacion", "inmuebles", "fiabilidad"]]
          .head(40).round(0).to_string(index=False))

dg = dd[dd["poblacion"] > 50_000]
res = (dg.groupby("cod_muni")
         .agg(distritos=("codigo", "count"),
              distritos_ok=("fiabilidad", lambda s: (s == "ok").sum()))
         .reset_index())
print("\n=== DISTRITOS EN CIUDADES DE MÁS DE 50.000 HAB. ===")
print("Distritos totales:", len(dg), "| con alquiler fiable (ok):", (dg["fiabilidad"] == "ok").sum())
for k in (1, 3, 5):
    print(f"Ciudades con al menos {k} distritos fiables: {(res['distritos_ok'] >= k).sum()}")

ok = g[g["fiabilidad"] == "ok"]
cols_v = ["nombre_muni", "provincia", "poblacion", "alquiler_mes", "renta_hogar", "alquiler_pct_renta"]
print("\n=== DONDE MÁS PESA EL ALQUILER (ciudades grandes con dato fiable) ===")
print(ok.sort_values("alquiler_pct_renta", ascending=False)[cols_v].head(8).round(1).to_string(index=False))
print("\n=== DONDE MENOS PESA ===")
print(ok.sort_values("alquiler_pct_renta")[cols_v].head(8).round(1).to_string(index=False))
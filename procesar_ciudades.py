from pathlib import Path
import numpy as np
import pandas as pd
import re

pd.set_option("display.width", 250)
pd.set_option("display.max_columns", 30)

base = Path(__file__).parent
origen = base / "datos_originales"
destino = base / "datos_limpios"
destino.mkdir(exist_ok=True)

CIUDADES = {
    "28079": ("Madrid", "renta_madrid.csv"),
    "46250": ("Valencia", "renta_valencia.csv"),
    "47186": ("Valladolid", "renta_valladolid.csv"),
}

valores_raros = set()

def num(s):
    """'17.411' -> 17411.0 ; cualquier marcador de dato no disponible -> NaN."""
    s = str(s).strip()
    # Un número válido en formato INE: dígitos con puntos de miles y coma decimal opcional
    if re.fullmatch(r"-?\d{1,3}(\.\d{3})*(,\d+)?|-?\d+(,\d+)?", s):
        return float(s.replace(".", "").replace(",", "."))
    if s not in ("", "nan"):
        valores_raros.add(s)   # lo anotamos para revisarlo
    return np.nan

def leer_csv(ruta):
    for cod in ("utf-8", "latin-1"):
        try:
            return pd.read_csv(ruta, sep=";", encoding=cod, dtype=str)
        except UnicodeDecodeError:
            continue
    raise ValueError(f"No se pudo leer {ruta}")

# ---------------- 1) RENTA ----------------
INDICADORES = {
    "Renta neta media por hogar": "renta_hogar",
    "Renta neta media por persona": "renta_persona",
    "Mediana de la renta por unidad de consumo": "renta_mediana_uc",
}

trozos = []
for cod_muni, (ciudad, fichero) in CIUDADES.items():
    df = leer_csv(origen / fichero)
    df["valor"] = df["Total"].map(num)
    df["año"] = df["Periodo"].astype(int)
    df["territorio"] = df["Secciones"].fillna(df["Distritos"]).fillna(df["Municipios"])
    df["nivel"] = np.where(df["Secciones"].notna(), "seccion",
                  np.where(df["Distritos"].notna(), "distrito", "municipio"))
    df["codigo"] = df["territorio"].str.split(" ", n=1).str[0]
    df["nombre"] = df["territorio"].str.split(" ", n=1).str[1]

    # Solo la ciudad (municipio + distritos), sin secciones por ahora
    df = df[df["codigo"].str.startswith(cod_muni) & df["nivel"].isin(["municipio", "distrito"])]
    df = df[df["Indicadores de renta media y mediana"].isin(INDICADORES)]
    df["indicador"] = df["Indicadores de renta media y mediana"].map(INDICADORES)
    df["ciudad"] = ciudad
    trozos.append(df[["ciudad", "nivel", "codigo", "nombre", "indicador", "año", "valor"]])
    print(f"{ciudad}: {df[df['nivel']=='distrito']['codigo'].nunique()} distritos en el archivo de renta")

renta_larga = pd.concat(trozos, ignore_index=True)
renta_larga.rename(columns={"año": "anio"}).to_csv(destino / "renta_largo.csv", index=False, encoding="utf-8-sig")

renta24 = (renta_larga[renta_larga["año"] == 2024]
           .pivot_table(index=["ciudad", "nivel", "codigo", "nombre"],
                        columns="indicador", values="valor")
           .reset_index())

# ---------------- 2) ALQUILER ----------------
ruta = origen / "Datos_municipios_2024.xlsx"
cols = {
    "BI_ALVHEPCO_TVC_24": "inmuebles",
    "ALQM2_LV_M_VC_24": "eur_m2",
    "ALQM2_LV_25_VC_24": "eur_m2_p25",
    "ALQM2_LV_75_VC_24": "eur_m2_p75",
    "ALQTBID12_M_VC_24": "alquiler_mes",
    "SLVM2_M_VC_24": "superficie_m2",
}
codigos_muni = [int(c) for c in CIUDADES]

muni = pd.read_excel(ruta, sheet_name="Municipios")
muni = muni[muni["CUMUN"].isin(codigos_muni)][["CUMUN"] + list(cols)]
muni["codigo"] = muni["CUMUN"].astype(str)

dist = pd.read_excel(ruta, sheet_name="Distritos")
dist = dist[dist["CUMUN"].isin(codigos_muni)][["CUDIS"] + list(cols)]
dist["codigo"] = dist["CUDIS"].astype(str)

alq = pd.concat([muni.drop(columns="CUMUN"), dist.drop(columns="CUDIS")], ignore_index=True)
alq = alq.rename(columns=cols)

# ---------------- 3) UNIÓN ----------------
final = renta24.merge(alq, on="codigo", how="outer", indicator=True)
print("\n¿Coinciden los códigos?")
print(final.groupby("ciudad", dropna=False)["_merge"].value_counts().to_string())
final = final.drop(columns="_merge")

final["alquiler_pct_renta"] = (final["alquiler_mes"] * 12 / final["renta_hogar"] * 100).round(1)

def fiabilidad(n):
    if pd.isna(n):
        return "sin_dato"
    if n >= 100:
        return "ok"
    if n >= 30:
        return "pocos_datos"
    return "no_mostrar"

final["fiabilidad"] = final["inmuebles"].map(fiabilidad)
final["año"] = 2024
final = final.sort_values(["ciudad", "nivel", "codigo"]).reset_index(drop=True)
final.rename(columns={"año": "anio"}).to_csv(destino / "ciudades_2024.csv", index=False, encoding="utf-8-sig")

# ---------------- 4) REVISIÓN ----------------
print("\n=== RESUMEN POR CIUDAD (municipio) ===")
res = final[final["nivel"] == "municipio"][
    ["ciudad", "renta_hogar", "renta_persona", "alquiler_mes", "eur_m2", "alquiler_pct_renta"]]
print(res.round(2).to_string(index=False))

print("\n=== Nº DE DISTRITOS POR CIUDAD Y FIABILIDAD ===")
print(final[final["nivel"] == "distrito"].groupby(["ciudad", "fiabilidad"]).size().to_string())

print("\n=== % ALQUILER SOBRE RENTA: 3 DISTRITOS MÁS ALTOS Y 3 MÁS BAJOS POR CIUDAD ===")
d = final[(final["nivel"] == "distrito") & (final["fiabilidad"] == "ok")]
for ciudad, g in d.groupby("ciudad"):
    g = g.sort_values("alquiler_pct_renta")
    print(f"\n{ciudad}")
    print(pd.concat([g.head(3), g.tail(3)])[["codigo", "renta_hogar", "alquiler_mes",
                                              "alquiler_pct_renta"]].to_string(index=False))

print("\nArchivos guardados en:", destino)
print("\nMarcadores no numéricos encontrados en la columna Total:", valores_raros)
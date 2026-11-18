from pathlib import Path
import pandas as pd

pd.set_option("display.width", 250)
pd.set_option("display.max_columns", 30)

carpeta = Path(__file__).parent
ruta = carpeta / "datos_originales" / "Datos_municipios_2024.xlsx"

CIUDADES = [28079, 46250, 47186]  # Madrid, Valencia, Valladolid

# 1) Municipios: evolución del alquiler mediano en pisos (€/m2)
muni = pd.read_excel(ruta, sheet_name="Municipios")
ciudades = muni[muni["CUMUN"].isin(CIUDADES)]
print("Ciudades encontradas:", ciudades["NMUN"].tolist())

print("\n=== EVOLUCIÓN ALQUILER MEDIANO PISOS (€/m2 al mes) ===")
cols_evol = [f"ALQM2_LV_M_VC_{a}" for a in range(11, 25)]
evol = ciudades.set_index("NMUN")[cols_evol]
evol.columns = [f"20{c[-2:]}" for c in evol.columns]
print(evol.T.round(2))

print("\n=== DATOS 2024 (pisos) ===")
cols_2024 = ["NMUN", "BI_ALVHEPCO_TVC_24", "ALQM2_LV_M_VC_24",
             "ALQM2_LV_25_VC_24", "ALQM2_LV_75_VC_24",
             "ALQTBID12_M_VC_24", "SLVM2_M_VC_24"]
print(ciudades[cols_2024].round(2).to_string(index=False))

# 2) Distritos de las 3 ciudades
dist = pd.read_excel(ruta, sheet_name="Distritos")
dist = dist[dist["CUMUN"].isin(CIUDADES)]

print("\n=== NÚMERO DE DISTRITOS POR CIUDAD ===")
print(dist.groupby("LITMUN")["CUDIS"].count())

print("\n=== DISTRITOS (2024, pisos) ===")
cols_dist = ["LITMUN", "CUDIS", "BI_ALVHEPCO_TVC_24",
             "ALQM2_LV_M_VC_24", "ALQTBID12_M_VC_24"]
print(dist[cols_dist].round(2).to_string(index=False))

print("\nDistritos sin dato de alquiler 2024:",
      dist["ALQM2_LV_M_VC_24"].isna().sum())
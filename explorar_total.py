from pathlib import Path
import pandas as pd

carpeta = Path(__file__).parent / "datos_originales"

for nombre in ["renta_total.csv", "demograficos_total.csv"]:
    ruta = carpeta / nombre
    print("\n=====", nombre, "|", round(ruta.stat().st_size / 1e6), "MB")
    filas = 0
    municipios = set()
    for i, trozo in enumerate(pd.read_csv(ruta, sep=";", encoding="utf-8",
                                          encoding_errors="replace", dtype=str,
                                          chunksize=500_000)):
        if i == 0:
            print("Columnas:", list(trozo.columns))
            print(trozo.head(5).to_string())
        filas += len(trozo)
        if "Municipios" in trozo.columns:
            municipios.update(trozo["Municipios"].dropna().unique())
    print("Filas:", filas, "| municipios distintos:", len(municipios))
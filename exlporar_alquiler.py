from pathlib import Path
import pandas as pd

carpeta = Path(__file__).parent
ruta = carpeta / "datos_originales" / "Datos_municipios_2024.xlsx"

print("Buscando:", ruta)
print("¿Existe?", ruta.exists())

if ruta.exists():
    xls = pd.ExcelFile(ruta)
    print("Hojas del archivo:", xls.sheet_names)

    for hoja in xls.sheet_names:
        df = xls.parse(hoja, nrows=5)
        print("\n--- Hoja:", hoja)
        print("Columnas:", list(df.columns))
        print(df.head())
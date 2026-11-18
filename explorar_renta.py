from pathlib import Path
import pandas as pd

pd.set_option("display.width", 250)
pd.set_option("display.max_columns", 30)
pd.set_option("display.max_colwidth", 60)

carpeta = Path(__file__).parent / "datos_originales"
archivo = carpeta / "renta_valladolid.csv"   # cambia esto si tu archivo se llama distinto

print("¿Existe?", archivo.exists())

# El INE a veces usa utf-8 y a veces latin-1: probamos los dos
for codificacion in ("utf-8", "latin-1"):
    try:
        df = pd.read_csv(archivo, sep=";", encoding=codificacion)
        print("Codificación que funciona:", codificacion)
        break
    except UnicodeDecodeError:
        continue

print("\nFilas:", len(df), "| Columnas:", len(df.columns))
print("\nNombres de columnas:")
print(list(df.columns))

print("\nPrimeras 12 filas:")
print(df.head(12).to_string())

# Para cada columna de texto, cuántos valores distintos tiene y ejemplos
print("\nValores distintos por columna (con ejemplos):")
for col in df.columns:
    n = df[col].nunique()
    ejemplos = df[col].dropna().unique()[:6]
    print(f"- {col}: {n} distintos | ejemplos: {list(ejemplos)}")
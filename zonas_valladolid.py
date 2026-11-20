"""Barrios (zonas estadísticas del Ayuntamiento) de los distritos de Valladolid -> datos_limpios/zonas_nombradas.csv

Los 12 distritos del Ayuntamiento son los distritos censales del INE (el documento de límites los llama
"distritos censales" y la población de cada uno coincide con el ADRH 2024 con diferencias de 0-4 %).
Las 47 zonas estadísticas tienen nombre, pero el Ayuntamiento no publica a qué distrito pertenece cada una
y algunas cruzan límites de distrito. Por eso:
  1. Se propone qué zonas forman cada distrito leyendo los documentos oficiales de límites
     (datos_municipales/47186_valladolid_limites_de_*.doc).
  2. Solo se acepta si la suma de la población de esas zonas es EXACTAMENTE la del distrito
     (padrón municipal a 1-I-2024, los dos Excel del Ayuntamiento). Si no cuadra, el distrito se queda
     con código postal y calles (preparar_zonas.py).
Uso: python zonas_valladolid.py
"""
import csv
import sys

import pandas as pd

from config import DATOS

BASE = DATOS.parent / "datos_municipales"
F_ZONAS = BASE / "47186_valladolid_poblacion_por_zonas_estadisticas_1986-2025.xls"
F_DIST = BASE / "47186_valladolid_poblacion_por_distritos_1981-2025.xls"
SALIDA = DATOS / "zonas_nombradas.csv"
COLUMNA = "1-I-2024(*)"
FUENTE = ("Ayuntamiento de Valladolid, Observatorio Urbano: 'Evolución de la población por Zonas Estadísticas desde 1986' y "
          "'Evolución de la población por Distritos desde 1981' (actualizados el 13/07/2026) y documentos de delimitación "
          "de distritos censales y zonas estadísticas; CC BY 3.0 ES (portal Open Data del Ayuntamiento), consultado el 20/11/2026")
CITA = "Ayuntamiento de Valladolid, zonas estadísticas (CC BY 3.0 ES)"

# Zonas (clave del Ayuntamiento) que, según los documentos de límites, forman cada distrito.
PROPUESTA = {
    3: ["2"],                                                   # mismo límite que la zona Caño Argales
    10: ["13", "14", "15", "15B", "23", "24", "24B", "25", "26", "27"],  # margen derecha del Pisuerga
    12: ["40", "41", "42"],                                     # entidades de población (lo dice el documento)
    6: ["7", "9", "18", "37", "38", "39"],                      # entre Labradores, Gabriel y Galán, el Esgueva y la Avenida de Soria
    8: ["11", "12", "12B", "21", "22"],                         # Pilarica y Belén quedan fuera (van con el distrito 7)
    11: ["28", "29", "30", "31", "32", "34", "35"],             # entre el Pisuerga, Puente Colgante, Arco de Ladrillo y la Avenida de Madrid
    9: ["4", "5", "6"],                                         # NO cuadra: parte de la zona Universidad cae en este distrito
}
# Distritos 1, 2, 4, 5, 7 y 9: alguna zona (Centro, Universidad, Campo Grande...) está repartida entre
# varios distritos, así que no se pueden describir con zonas enteras. Se quedan con código postal y calles.


def leer(f, fila_cab, clave_col):
    t = pd.read_excel(f, header=None)
    cab = [str(x).strip() for x in t.iloc[fila_cab]]
    col = cab.index(COLUMNA)
    out = {}
    for i in range(fila_cab + 1, len(t)):
        k = str(t.iloc[i, clave_col]).strip()
        if k in ("", "nan", "Total", "Total Municipio"):
            continue
        k = k[:-2] if k.endswith(".0") else k
        if pd.isna(t.iloc[i, col]) or str(t.iloc[i, 2]).strip() == "No consta":
            continue
        out[k] = (str(t.iloc[i, 2]).strip(), int(t.iloc[i, col]))
    return out


def main():
    zonas = leer(F_ZONAS, 4, 1)
    dist = leer(F_DIST, 8, 1)
    filas = []
    for d, claves in sorted(PROPUESTA.items()):
        suma = sum(zonas[k][1] for k in claves)
        pob = dist[str(d)][1]
        ok = suma == pob
        nombres = [zonas[k][0] for k in sorted(claves, key=lambda k: -zonas[k][1])]
        print(f"Distrito {d:2}: población {pob} | suma de zonas {suma} -> {'COINCIDE' if ok else 'NO coincide'} ({', '.join(nombres)})")
        if ok:
            filas.append({"codigo": f"47186{d:02d}", "zonas": "|".join(nombres), "fuente": FUENTE, "cita": CITA})
    otras = []
    if SALIDA.exists():
        otras = [r for r in csv.DictReader(open(SALIDA, encoding="utf-8")) if not r["codigo"].startswith("47186")]
    with open(SALIDA, "w", encoding="utf-8", newline="") as out:
        w = csv.DictWriter(out, fieldnames=["codigo", "zonas", "fuente", "cita"])
        w.writeheader()
        w.writerows(otras + filas)
    print(f"Escritos {len(filas)} distritos de Valladolid en {SALIDA.name}")


if __name__ == "__main__":
    main()

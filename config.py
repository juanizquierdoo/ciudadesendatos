"""Configuración común del pipeline de ciudadesendatos.

Cuando salgan datos nuevos (p. ej. 2025), normalmente basta con:
  1. Poner los archivos nuevos en datos_originales/.
  2. Cambiar ANIO (y, si cambia el nombre, ARCHIVO_SERPAVI) aquí.
  3. Ejecutar:  python actualizar.py
"""
from pathlib import Path

ANIO = 2024                     # último año con alquiler (SERPAVI) y renta (INE ADRH)
ANIO_INICIO_ALQUILER = 2011     # primer año de la serie SERPAVI
UMBRAL_POBLACION = 50_000       # nivel 1: ciudades de más de este número de habitantes

BASE = Path(__file__).parent
ORIGEN = BASE / "datos_originales"
DATOS = BASE / "datos_limpios"

ARCHIVO_SERPAVI = ORIGEN / f"Datos_municipios_{ANIO}.xlsx"
ARCHIVO_RENTA = ORIGEN / "renta_total.csv"
ARCHIVO_DEMOGRAFIA = ORIGEN / "demograficos_total.csv"

# Salidas
DEMOGRAFIA = DATOS / f"demografia_municipios_{ANIO}.csv"
RENTA_LARGO = DATOS / "renta_nacional_largo.csv"
MUNICIPIOS = DATOS / f"municipios_{ANIO}.csv"
DISTRITOS = DATOS / f"distritos_{ANIO}.csv"
JSON_NIVEL1 = DATOS / "ciudades_nivel1.json"


def yy(anio=ANIO):
    """Sufijo de dos cifras de las columnas del SERPAVI: 2024 -> '24'."""
    return f"{anio % 100:02d}"


# Valores de referencia que SIEMPRE deben reproducirse (solo para ANIO = 2024).
# Si cambias de año, añade los nuevos valores tras comprobarlos a mano.
REFERENCIA = {
    2024: {
        "28079": ("Madrid", 868.75, 53213, 19.6),
        "46250": ("Valencia", 680.83, 42374, 19.3),
        "47186": ("Valladolid", 530.83, 39685, 16.1),
    },
}

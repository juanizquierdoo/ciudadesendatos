"""Ejecuta todo el pipeline de ciudadesendatos con un solo comando.

Uso (desde la carpeta del proyecto):
    python actualizar.py              # pipeline completo + tests
    python actualizar.py --desde 3    # empieza en el paso 3 (si los CSV del INE no han cambiado)

Pasos:
    1. procesar_nacional.py  lee los CSV grandes del INE (renta y demografía)
    2. unir_nacional.py      une renta, demografía y alquiler (SERPAVI)
    3. preparar_zonas.py     códigos postales y calles de cada distrito (callejero del INE)
    4. preparar_json.py      selecciona ciudades y comprueba los valores de referencia
    5. preparar_comunidades.py  alquiler oficial por comunidad autónoma (SERPAVI, hoja CCAA)
    6. mapa_distritos.py     posición de los distritos en el mapa esquemático (callejero del INE + calles de OSM)
    7. generar_web.py        genera la carpeta web/
    8. tests/ejecutar_tests.py

Se para en el primer paso que falle. El año de los datos se cambia en config.py.
"""
import subprocess
import sys
import time
from pathlib import Path

from config import ANIO

BASE = Path(__file__).parent
PASOS = ["procesar_nacional.py", "unir_nacional.py", "preparar_zonas.py", "preparar_json.py", "preparar_comunidades.py",
         "mapa_distritos.py", "generar_web.py", "tests/ejecutar_tests.py"]


def main():
    desde = 1
    if "--desde" in sys.argv:
        desde = int(sys.argv[sys.argv.index("--desde") + 1])
    print(f"Actualizando ciudadesendatos con datos de {ANIO}\n")
    t0 = time.time()
    for i, paso in enumerate(PASOS, 1):
        if i < desde:
            print(f"[{i}/{len(PASOS)}] {paso}: omitido")
            continue
        print(f"[{i}/{len(PASOS)}] {paso} ...", flush=True)
        t = time.time()
        r = subprocess.run([sys.executable, str(BASE / paso)], cwd=BASE)
        if r.returncode != 0:
            print(f"\nERROR en {paso} (código {r.returncode}). Se detiene la actualización.")
            print("La web/ puede haber quedado a medias: no la publiques hasta corregirlo.")
            sys.exit(r.returncode)
        print(f"    terminado en {time.time() - t:.0f} s\n")
    print(f"Todo correcto en {time.time() - t0:.0f} s. Revisa los cambios con 'git diff --stat' antes de publicar.")


if __name__ == "__main__":
    main()

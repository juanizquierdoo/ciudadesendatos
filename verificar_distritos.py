"""Verifica los nombres de distrito de un ayuntamiento antes de usarlos (B-23).

Compara las secciones censales (distrito + sección) de un fichero municipal con las
del Atlas de Distribución de Renta de los Hogares (ADRH) del INE. Solo si coinciden
TODAS, los códigos de distrito municipales son los mismos que usa la web y los nombres
se pueden dar por buenos.

Uso (desde la carpeta del proyecto):
    python verificar_distritos.py datos_municipales/48020_bilbao_secciones_2022.csv
    python verificar_distritos.py datos_municipales/48020_bilbao_secciones_2022.csv --escribir --fuente "texto de la fuente"

El fichero municipal se guarda en datos_municipales/ con el nombre <cod_muni>_<ciudad>_... .csv
y tres columnas: distrito (2 cifras), seccion (3 cifras), nombre_distrito (tal como lo da
el ayuntamiento). Se puede convertir a este formato a mano o con un script corto; nunca se
cambian los códigos ni los nombres, solo el formato.

Con --escribir (y solo si la comprobación sale bien) sustituye las filas de ese municipio
en datos_limpios/nombres_distritos.csv. Después hay que ejecutar: python actualizar.py --desde 3
"""
import argparse
import csv
import sys
from pathlib import Path

import pandas as pd

from config import ANIO, ARCHIVO_RENTA, DATOS

CACHE = DATOS / f"secciones_adrh_{ANIO}.csv"
NOMBRES = DATOS / "nombres_distritos.csv"
PALABRAS_MINUSCULA = {"de", "del", "la", "las", "los", "el", "y", "i", "d", "l"}


def secciones_ine():
    """Conjunto de secciones (10 cifras) del ADRH del año ANIO. Se guarda en caché la primera vez."""
    if not CACHE.exists():
        print(f"Leyendo {ARCHIVO_RENTA.name} por trozos (solo la primera vez, 1-2 minutos)...", flush=True)
        filas = set()
        for ch in pd.read_csv(ARCHIVO_RENTA, sep=";", dtype=str, chunksize=500_000,
                              usecols=["Municipios", "Distritos", "Secciones", "Periodo"]):
            ch = ch[(ch["Periodo"] == str(ANIO)) & ch["Secciones"].notna()]
            filas.update(s.split()[0] for s in ch["Secciones"])
        pd.DataFrame(sorted(filas), columns=["seccion"]).to_csv(CACHE, index=False)
    return set(pd.read_csv(CACHE, dtype=str)["seccion"])


def nombre_bonito(n):
    """Solo cambia mayúsculas: 'BASURTU-ZORROTZA' -> 'Basurtu-Zorrotza'. Si ya viene en mayúsculas y minúsculas, se deja igual."""
    n = " ".join(n.split())
    if n != n.upper():
        return n
    partes = []
    for i, p in enumerate(n.lower().split(" ")):
        p = "-".join(x.capitalize() for x in p.split("-"))
        partes.append(p.lower() if i > 0 and p.lower() in PALABRAS_MINUSCULA else p)
    return " ".join(partes)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("fichero")
    ap.add_argument("--escribir", action="store_true")
    ap.add_argument("--fuente", default="")
    a = ap.parse_args()

    f = Path(a.fichero)
    cod = f.name[:5]
    if not cod.isdigit():
        sys.exit("El nombre del fichero debe empezar por el código INE del municipio (5 cifras).")
    mun = pd.read_csv(f, dtype=str, encoding="utf-8")
    mun["distrito"] = mun["distrito"].str.strip().str.zfill(2)
    mun["seccion"] = mun["seccion"].str.strip().str.zfill(3)
    secc_mun = set(cod + mun["distrito"] + mun["seccion"])
    secc_ine = {s for s in secciones_ine() if s.startswith(cod)}

    print(f"Municipio {cod}: {len(secc_mun)} secciones en el fichero municipal, {len(secc_ine)} en el ADRH {ANIO}.")
    ok = True
    if secc_mun - secc_ine:
        ok = False
        print("  Solo en el fichero municipal:", ", ".join(sorted(secc_mun - secc_ine)))
    if secc_ine - secc_mun:
        ok = False
        print("  Solo en el INE:", ", ".join(sorted(secc_ine - secc_mun)))
    por_distrito = mun.groupby("distrito")["nombre_distrito"].apply(lambda s: sorted(set(x.strip() for x in s)))
    for d, ns in por_distrito.items():
        if len(ns) != 1:
            ok = False
            print(f"  El distrito {d} tiene más de un nombre: {ns}")
    if not ok:
        print("RESULTADO: NO COINCIDE. No se añaden los nombres.")
        sys.exit(1)

    nombres = {cod + d: nombre_bonito(ns[0]) for d, ns in por_distrito.items()}
    print(f"RESULTADO: COINCIDEN las {len(secc_mun)} secciones. Distritos:")
    for c, n in nombres.items():
        print(f"  {c}  {n}")

    if a.escribir:
        if not a.fuente:
            sys.exit("Falta --fuente: cada nombre tiene que llevar su fuente y licencia.")
        filas = list(csv.DictReader(open(NOMBRES, encoding="utf-8")))
        filas = [r for r in filas if not r["codigo"].startswith(cod)]
        verif = f"códigos verificados: las {len(secc_mun)} secciones censales coinciden con el ADRH {ANIO} del INE"
        filas += [{"codigo": c, "nombre_distrito": n, "fuente": f"{a.fuente}; {verif}"} for c, n in nombres.items()]
        with open(NOMBRES, "w", encoding="utf-8", newline="") as out:
            w = csv.DictWriter(out, fieldnames=["codigo", "nombre_distrito", "fuente"])
            w.writeheader()
            w.writerows(filas)
        print(f"Escritos {len(nombres)} nombres en {NOMBRES.name}. Ahora: python actualizar.py --desde 3")


if __name__ == "__main__":
    main()

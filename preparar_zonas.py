"""Zonas de cada distrito: códigos postales, calles principales y núcleos (Callejero del Censo Electoral, INE).

Para que el lector sepa qué zona es "Distrito 8" sin inventar nombres, cada distrito se describe con:
  - los códigos postales que aparecen en al menos el 20 % de sus secciones censales (máximo 4);
  - sus 3 calles principales: las que pasan por más secciones del distrito (desempate: más tramos);
  - los núcleos de población (entidades singulares del INE) distintos del principal del municipio.

Entrada: datos_originales/caj_esp_<MMAAAA>/ (TRAM y VIAS). Se descarga de
https://www.ine.es/dyngs/DAB/es/index.htm?cid=1390 (ficheros nacionales). Diseño de registro: Dis_nuevo.xlsx.
Salida:  datos_limpios/zonas_distritos.csv (codigo, cps, calles, nucleos, secciones, fecha_callejero).
Si no está el callejero, avisa y no hace nada (la web sigue mostrando "Distrito N").
"""
import collections
import csv
import re
import sys

import pandas as pd

from config import DATOS, MUNICIPIOS, ORIGEN, UMBRAL_POBLACION

SALIDA = DATOS / "zonas_distritos.csv"
MIN_CP = 0.20         # un código postal se muestra si aparece en al menos el 20 % de las secciones del distrito
MAX_CP = 4
N_CALLES = 3
MIN_TRAMOS_NUCLEO = 3

# Tipos de vía que se muestran delante del nombre (solo abreviaturas sin ambigüedad).
# Las de "calle" (CALLE, C, C/, RUA, CARRE...) se omiten: el nombre basta.
TIPOS = {"PLAZA": "Plaza", "PL": "Plaza", "PRAZA": "Praza", "PLAÇA": "Plaça", "PASEO": "Paseo", "AVDA": "Avenida",
         "AVGDA": "Avinguda", "RONDA": "Ronda", "RBLA": "Rambla", "GTA": "Glorieta", "CTRA": "Carretera",
         "TRVA": "Travesía", "PSAJE": "Pasaje", "CMNO": "Camino", "CAMI": "Camí", "PQUE": "Parque", "VIA": "Vía",
         "CUSTA": "Cuesta", "SENDA": "Senda"}
# Tipos que no son calles (parajes, urbanizaciones, diseminados...): no cuentan como "calle principal".
NO_CALLE = {"LUGAR", "LLOC", "URB", "PRAJE", "FINCA", "PTDA", "CRTJO", "MASIA", "PAGO", "ZONA", "POLIG", "BARRO",
            "BARDA", "ENTD", "CSRIO", "APTOS", "DSEMN", "DISEM", "EXTRR", "GRUP", "GRUPO", "CJTO", "PG", "PRAJE",
            "PARAJ", "COLEC", "AFUER", "AREA", "SECTOR", "POBLA", "CRRIL", "VREDA", "PAGO", "BARRI"}
MINUS = {"de", "del", "la", "las", "los", "el", "y", "i", "e", "a", "da", "do", "das", "dos", "en", "al", "d'", "l'"}


def bonito(s):
    """'PORTILLO DE BALBOA' -> 'Portillo de Balboa'; 'PINARILLO (EL)' -> 'El Pinarillo'. Solo mayúsculas/minúsculas."""
    s = " ".join(s.split())
    m = re.match(r"^(.*)\s\((EL|LA|LOS|LAS|L'|ELS|ES|SA|SES|O|A|OS|AS)\)$", s)
    if m:
        s = m.group(2) + ("" if m.group(2).endswith("'") else " ") + m.group(1)
    out = []
    for i, p in enumerate(s.lower().split(" ")):
        p = "-".join(x[:1].upper() + x[1:] for x in p.split("-"))
        out.append(p.lower() if i > 0 and p.lower() in MINUS else p)
    if len(out) > 1 and re.fullmatch(r"[ivxl]+", out[-1].lower()):
        out[-1] = out[-1].upper()          # números romanos al final: "Juan Carlos I"
    return " ".join(out)


def buscar_callejero():
    dirs = sorted(ORIGEN.glob("caj_esp_*"))
    if not dirs:
        return None, None, None
    d = dirs[-1]
    tram = next(d.glob("TRAM.*"), None)
    vias = next(d.glob("VIAS.*"), None)
    m = re.search(r"\.D(\d{2})(\d{2})(\d{2})\.", tram.name) if tram else None
    fecha = f"{m.group(3)}/{m.group(2)}/20{m.group(1)}" if m else ""
    return tram, vias, fecha


def main():
    tram, vias, fecha = buscar_callejero()
    if not tram or not vias:
        print("AVISO: no está el callejero del INE en datos_originales/caj_esp_*/; no se generan zonas.")
        return
    mun = pd.read_csv(MUNICIPIOS, dtype={"cod_muni": str}, encoding="utf-8-sig")
    cods = set(mun[(mun["poblacion"] > UMBRAL_POBLACION) & (mun["fiabilidad"] == "ok")]["cod_muni"])

    nombres_via = {}
    with open(vias, encoding="latin1") as f:
        for l in f:
            if l[:5] in cods:
                nombres_via[(l[:5], l[47:52])] = (l[52:57].strip(), l[57:107].strip())

    secc_via = collections.defaultdict(lambda: collections.defaultdict(set))
    tramos_via = collections.defaultdict(collections.Counter)
    secc_cp = collections.defaultdict(lambda: collections.defaultdict(set))
    secciones = collections.defaultdict(set)
    nucleos = collections.defaultdict(collections.Counter)
    nucleo_mun = collections.defaultdict(collections.Counter)
    with open(tram, encoding="latin1") as f:
        for l in f:
            cm = l[:5]
            if cm not in cods:
                continue
            dist = cm + l[70:72]                       # bloque de la situación actual (posiciones 71-75)
            secc = l[72:75]
            via = l[160:165]
            cp = l[257:262]
            ent = l[110:135].strip()
            secciones[dist].add(secc)
            secc_via[dist][via].add(secc)
            tramos_via[dist][via] += 1
            if cp.strip() and cp != "00000":
                secc_cp[dist][cp].add(secc)
            nucleos[dist][ent] += 1
            nucleo_mun[cm][ent] += 1

    filas = []
    for dist in sorted(secciones):
        cm = dist[:5]
        ns = len(secciones[dist])
        cps = sorted(secc_cp[dist], key=lambda k: (-len(secc_cp[dist][k]), k))
        cps_ok = [k for k in cps if len(secc_cp[dist][k]) / ns >= MIN_CP][:MAX_CP] or cps[:1]
        candidatas = [v for v in secc_via[dist] if nombres_via.get((cm, v), ("", ""))[0] not in NO_CALLE
                      and nombres_via.get((cm, v), ("", ""))[1]]
        candidatas.sort(key=lambda v: (-len(secc_via[dist][v]), -tramos_via[dist][v], nombres_via[(cm, v)][1]))
        calles = []
        for v in candidatas[:N_CALLES]:
            tipo, nom = nombres_via[(cm, v)]
            calles.append((TIPOS[tipo] + " " if tipo in TIPOS else "") + bonito(nom))
        principal = nucleo_mun[cm].most_common(1)[0][0]
        nucs = [bonito(e) for e, k in nucleos[dist].most_common() if e and e != principal and k >= MIN_TRAMOS_NUCLEO][:3]
        filas.append({"codigo": dist, "cps": "|".join(cps_ok), "calles": "|".join(calles),
                      "nucleos": "|".join(nucs), "secciones": ns, "fecha_callejero": fecha})
    with open(SALIDA, "w", encoding="utf-8", newline="") as out:
        w = csv.DictWriter(out, fieldnames=list(filas[0]))
        w.writeheader()
        w.writerows(filas)
    print(f"Zonas de {len(filas)} distritos de {len({f['codigo'][:5] for f in filas})} municipios "
          f"(callejero del INE a {fecha}) -> {SALIDA.name}")


if __name__ == "__main__":
    main()

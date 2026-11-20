# PROYECTO: ciudadesendatos

Documento vivo. Se lee al empezar cada sesión y se actualiza al terminar.
Las reglas completas están en INSTRUCCIONES_PROYECTO.md; aquí va el **estado**.

Última actualización: 18/11/2026 (Fase 0, auditoría).

## Fase actual
**Fase 0 - Auditoría: terminada y entregada.** Hay que esperar a que Juan apruebe el informe (INFORME_FASE0.md) antes de empezar la Fase 1.

## Qué hay
| Elemento | Estado |
|---|---|
| Ciudades con página (más de 50.000 hab., alquiler fiable) | 151 |
| Ciudades con desglose por distrito | 130 (843 distritos) |
| Distritos con nombre oficial | 50 (Madrid 21, Valencia 19, Barcelona 10) |
| Páginas de la web | 170: portada, 4 rankings, índice de comunidades, 13 comunidades y 151 ciudades |
| Mapa | Solo Madrid (esquemático, no son los límites reales) |
| Publicada | **Sí, desde el 20/11/2026** en https://ciudadesendatos.es (HTTPS, http y www redirigen). Dominio ciudadesendatos.es (DonDominio). BASE_URL activo: sitemap, canonical y CNAME se generan. Despliegue con GitHub Pages vía `.github/workflows/publicar.yml` |
| Páginas legales y analítica | No existen |
| Git | Repositorio local desde el 18/11/2026. Remoto previsto: github.com/juanizquierdoo/ciudadesendatos (público, lo crea Juan) |

## Cómo se ejecuta
Desde la carpeta del proyecto, en este orden:
```
python procesar_nacional.py    # lee los CSV grandes del INE por trozos -> renta_nacional_largo.csv, demografia_municipios_2024.csv
python unir_nacional.py        # une renta, demografía y SERPAVI -> municipios_2024.csv, distritos_2024.csv
python preparar_json.py        # selecciona las ciudades -> ciudades_nivel1.json (comprueba los valores de referencia)
python preparar_comunidades.py # alquiler por comunidad (SERPAVI, hoja CCAA) -> comunidades.json
python generar_web.py          # genera web/ (se borra y se rehace entera)
python tests/ejecutar_tests.py # comprobaciones automáticas
```
Tiempo total medido el 18/11/2026: menos de 2 minutos.
O todo de una vez: `python actualizar.py` (o `python actualizar.py --desde 3` para saltarse la lectura de los CSV grandes del INE). El año se cambia en `config.py`.

## Valores de referencia (comprobados el 18/11/2026)
| Ciudad | Alquiler mediano | Renta neta hogar | Alquiler/renta | Resultado |
|---|---|---|---|---|
| Madrid | 868,75 € | 53.213 € | 19,6 % | OK |
| Valencia | 680,83 € | 42.374 € | 19,3 % | OK |
| Valladolid | 530,83 € | 39.685 € | 16,1 % | OK |

El pipeline es reproducible: al ejecutarlo de nuevo, los datos limpios y la web salen idénticos. Solo cambian la fecha "generado" del JSON y los saltos de línea (Windows/Linux).

## Archivos
- `datos_originales/`: SOLO LECTURA. Fuera de git (pesan mucho y se pueden volver a descargar).
- `datos_limpios/`: salida del pipeline. `renta_nacional_largo.csv` y `demografia_municipios_2024.csv` están fuera de git porque son intermedios pesados.
  - `ciudades_2024.csv` y `renta_largo.csv` son restos de la versión de 3 ciudades (`procesar_ciudades.py`). Ningún script del pipeline actual los usa (B-08).
- `web/`: se GENERA. No se edita a mano.
- `tests/ejecutar_tests.py`: comprobaciones sin dependencias externas.
- Scripts de exploración (`explorar_*.py`, `exlporar_alquiler.py`), `procesar_ciudades.py` y `unir_valladolid.py`: de la etapa inicial, no forman parte del pipeline.

## Decisiones tomadas
Ver INSTRUCCIONES_PROYECTO.md, apartado "Decisiones tomadas". Añadidas en esta sesión:
- 18/11/2026: los tests son un script de Python sin dependencias (sin pytest) para que funcionen en Windows sin instalar nada.
- 18/11/2026: los fallos conocidos aparecen como PENDIENTE en los tests y enlazan a una entrada del backlog. No se ocultan.
- 19/11/2026: licencia propia CC BY 4.0 para los datos elaborados y los textos de ciudadesendatos (pie y JSON-LD). Los datos de origen mantienen la licencia de sus fuentes.

## Fase actual (actualizado)
Fase 0 aprobada el 18/11/2026. Juan va a comprar un dominio. Corregidos los riesgos 2, 4 y 5; el 3 (nombres de distrito) está en curso, ciudad a ciudad.

## Próximo paso (19/11/2026)
Decidido por Juan: los nombres de distrito se continúan en otra sesión, por este orden:
1. B-23: crear `verificar_distritos.py`, que compare las secciones censales (distrito + sección) de un fichero municipal con las del ADRH del INE y solo dé por buenos los nombres si coinciden todas, como se hizo con Barcelona.
2. Añadir ciudades por tandas, empezando por las más grandes: Sevilla, Bilbao, Córdoba… (Málaga necesita comparar geometrías: B-22).
3. B-20: documentar y verificar Madrid y Valencia.
En paralelo, cuando Juan tenga el dominio: Fase 1 (publicar en GitHub Pages, páginas legales y medición).

## Publicación (19/11/2026)
- Dominio: ciudadesendatos.es, comprado en DonDominio, solo dominio. Dirección principal sin www; www redirige.
- Hosting: GitHub Pages, publicado por GitHub Actions desde la carpeta `web/` de la rama main (`.github/workflows/publicar.yml`). Para actualizar la web: `python actualizar.py`, commit y `git push`.
- DNS en DonDominio: 4 registros A a 185.199.108.153, 185.199.109.153, 185.199.110.153, 185.199.111.153 (y AAAA 2606:50c0:8000::153 … 8003::153) para el dominio raíz, y CNAME `www` -> juanizquierdoo.github.io.
- Después de publicar: HTTPS obligatorio en Pages, verificar el dominio en GitHub, alta en Search Console con el sitemap, páginas legales y analítica (resto de la Fase 1), B-19.

## Páginas por comunidad autónoma (19/11/2026)
- Hecho B-18 (Juan lo aprobó en el hilo). Solo hay página para comunidades con 3 o más ciudades (constante MIN_CIUDADES_CCAA en generar_web.py). Las URL son /comunidades/<nombre>/; los nombres de la URL y el nombre corto están en CCAA_INFO.
- Siguiente: medir en Search Console (B-25) antes de hacer páginas por provincia (B-24).

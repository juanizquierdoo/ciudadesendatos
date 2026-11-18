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
| Páginas de la web | 156: portada, 4 rankings, 151 ciudades |
| Mapa | Solo Madrid (esquemático, no son los límites reales) |
| Publicada | **No**. BASE_URL está vacío, así que no hay sitemap ni canonical |
| Páginas legales y analítica | No existen |
| Git | Repositorio local desde el 18/11/2026, sin remoto |

## Cómo se ejecuta
Desde la carpeta del proyecto, en este orden:
```
python procesar_nacional.py    # lee los CSV grandes del INE por trozos -> renta_nacional_largo.csv, demografia_municipios_2024.csv
python unir_nacional.py        # une renta, demografía y SERPAVI -> municipios_2024.csv, distritos_2024.csv
python preparar_json.py        # selecciona las ciudades -> ciudades_nivel1.json (comprueba los valores de referencia)
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

## Fase actual (actualizado)
Fase 0 aprobada el 18/11/2026. Juan va a comprar un dominio. Corregidos los riesgos 2, 4 y 5; el 3 (nombres de distrito) está en curso, ciudad a ciudad.

## Próximo paso (anterior)
Que Juan revise INFORME_FASE0.md y apruebe (o reordene) la Fase 1.

# BACKLOG

Prioridad: A = antes de publicar, B = poco después, C = cuando toque.
Estado: pendiente / en curso / hecho.

## Antes de publicar (Fase 1)
| Id | Prio | Tarea | Por qué | Estado |
|---|---|---|---|---|
| B-01 | A | Añadir al pie de cada página la fecha de actualización de cada fuente (ADRH: nota de prensa 19/10/2026; SERPAVI: metadatos 08/07/2026) y la fecha de generación de la web | El Aviso legal del INE y las condiciones generales de reutilización piden mencionar la fecha de actualización cuando figura en el original. El test `fecha_actualizacion` está en PENDIENTE | pendiente |
| B-02 | A | Confirmar la licencia del fichero SERPAVI con una URL oficial y guardarla en FUENTES.md | El PDF del SERPAVI dice "Todos los derechos reservados" (se refiere a la publicación PDF, no necesariamente a la base de datos). INSTRUCCIONES dice que la reutilización está permitida, pero no hay enlace registrado. Otros conjuntos del mismo ministerio en datos.gob.es son CC BY 4.0 | pendiente |
| B-03 | A | Publicar: elegir dominio, BASE_URL, GitHub Pages, sitemap y canonical | Sin publicar no hay visitas | pendiente |
| B-04 | A | Páginas legales: aviso legal, privacidad y cookies; metodología y "sobre el proyecto" como páginas propias | LSSI y RGPD; además dan confianza (E-E-A-T). No es asesoramiento legal | pendiente |
| B-05 | B | Acortar el título de 37 páginas de ciudad que pasan de 70 caracteres (p. ej. Castelló de la Plana, 100) | Google los corta en los resultados. El test `titulo_largo` está en PENDIENTE | pendiente |
| B-06 | A | Medición: Google Search Console y una analítica sin cookies | Para medir la demanda real y no suponerla | pendiente |
| B-07 | A | Crear `actualizar.py`, que ejecute el pipeline completo y los tests con un solo comando | Lo piden las instrucciones; reduce errores | pendiente |

## Calidad y mantenimiento
| Id | Prio | Tarea | Por qué | Estado |
|---|---|---|---|---|
| B-08 | B | Mover a `antiguo/` los scripts de exploración, `procesar_ciudades.py`, `unir_valladolid.py`, `ciudades_2024.csv` y `renta_largo.csv` | Que nadie use por error datos obsoletos | pendiente |
| B-09 | B | Sacar el año (2024) y las columnas `_24` a una constante única | Hoy el año está escrito en varios scripts; al llegar los datos de 2025 habría que tocar cada uno | pendiente |
| B-10 | B | Separar el pipeline en módulos (alquiler, renta, demografía), cada uno con su ingesta y su registro de fuente | Arquitectura modular que piden las instrucciones; añadir un dato no debe obligar a rehacer los demás | pendiente |
| B-11 | B | Contrastar 2-3 códigos de distrito con el visor del INE y con el Ayuntamiento | El SERPAVI usa el seccionado del Censo 2021 y el ADRH es de 2024. Los códigos casan en 864 de 865 distritos, pero eso no garantiza que los límites sean iguales | pendiente |
| B-12 | B | Nombres de distrito para más ciudades (solo de fuentes oficiales con licencia) | 110 ciudades muestran "Distrito N"; aporta poco a quien busca su barrio | pendiente |
| B-13 | B | Revisar el ranking "peso del alquiler": los 8 primeros son de Málaga y casi todos de costa | Puede inducir a error (renta de residentes frente a demanda de fuera). Valorar un aviso destacado o separar los municipios turísticos | pendiente |
| B-14 | C | Probar la web en Firefox, Safari y un móvil real | Ya está probada en Chromium (escritorio y móvil, 18/11/2026); faltan los demás navegadores | pendiente |
| B-15 | C | Normalizar los saltos de línea (`.gitattributes`) | Al generar en Linux y en Windows, git ve todos los archivos como cambiados | hecho 18/11/2026 |

## Funcionalidades candidatas
El ranking puntuado está en INFORME_FASE0.md. Cada una necesita su ficha y la aprobación de Juan antes de empezar.

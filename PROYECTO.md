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
| Distritos con nombre oficial | 58 (Madrid 21, Valencia 19, Barcelona 10, Bilbao 8) |
| Páginas de la web | 170: portada, 4 rankings, índice de comunidades, 13 comunidades y 151 ciudades |
| Mapa | Solo Madrid (esquemático, no son los límites reales) |
| Publicada | **Sí, desde el 20/11/2026** en https://ciudadesendatos.es (HTTPS, http y www redirigen). Dominio ciudadesendatos.es (DonDominio). BASE_URL activo: sitemap, canonical y CNAME se generan. Despliegue con GitHub Pages vía `.github/workflows/publicar.yml` |
| Páginas legales y analítica | Aviso legal, privacidad y cookies en /aviso-legal/, /privacidad/ y /cookies/ (`paginas_legales.py`), con nombre y correo ciudadesendatos@gmail.com. Decidido por Juan (20/11/2026): NIF y domicilio solo cuando haya anuncios (ANUNCIOS = True). Sin analítica |
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

## Texto propio en las fichas (20/11/2026)
- `textos_ciudad.py` escribe en cada ficha la sección "Qué dicen los datos de <ciudad>", calculada solo con el JSON (B-17). Se genera desde la plantilla: las ciudades nuevas lo tienen sin hacer nada. Test: `tests/test_textos.py`.
- Siguiente: medir en Search Console, 3-4 semanas después de publicarlo, si suben las impresiones de las fichas.

## Nombres de distrito por tandas (20/11/2026)
- Hecho B-23: `python verificar_distritos.py datos_municipales/<cod>_<ciudad>_....csv` y, si coincide, lo mismo con `--escribir --fuente "..."`; después `python actualizar.py --desde 3`.
- Tanda 1: Bilbao añadida. Sevilla y Zaragoza sin fuente válida. Siguientes: Córdoba, Murcia, Palma, Las Palmas, Alicante, Vigo, Gijón, Vitoria, A Coruña, Granada.
- Nota técnica: desde esta sesión no hay acceso directo a internet; los ficheros municipales se leen con el navegador integrado.
- Hecho B-27: los distritos sin nombre se identifican con código postal y calles principales (callejero del INE, `preparar_zonas.py`). Al salir un callejero nuevo (enero y julio), descargarlo en datos_originales/ y ejecutar `python actualizar.py --desde 3`.
- Hecho B-26: la ficha cita la fuente de los nombres (columna `cita` de nombres_distritos.csv). Al añadir una ciudad, rellenar esa columna.

## Rankings temáticos (20/11/2026)
- Hecho B-29: `rankings_temas.py` genera 5 rankings pensados para búsquedas concretas (subida del alquiler, sueldo necesario, distritos por renta y por alquiler, ciudades más jóvenes). Para añadir otro: una función `pagina_x(gw, todas, rutas)`, una línea en TEMAS y otra en PAGINAS; el test lo recoge solo si se añade a `esperado`.
- La demanda de búsqueda de cada página es una hipótesis: medirla en Search Console (B-30) antes de crear más.

## Barrios en más ciudades (20/11/2026)
- `python zonas_ciudades.py` y después `python actualizar.py --desde 4`. Hecho: Sevilla y Zaragoza. Málaga publicada (su lista de barrios con CC BY-SA 4.0, aceptado por Juan). Las Palmas hecha (cruce por calles). El resto, con OpenStreetMap: `python zonas_osm.py` (necesita los archivos de `datos_municipales/osm`, que Juan baja con `descargar_osm.html`). El buscador de la portada encuentra barrios. Antes: Murcia, Palma, Córdoba, Alicante, Vigo, Gijón, Granada (B-32). Detalle y método en FUENTES.md, fuente 6.

## Diseño (20/11/2026)
- La cabecera y el pie son comunes (`cabecera()` y `pie()` en `generar_web.py`) y los usan también `rankings_temas.py` y `paginas_legales.py`. Para cambiar el aspecto, tocar solo esas funciones y la constante `CSS`. Muestra aprobada por Juan: capturas en la carpeta del proyecto `rediseno/`.

## Fase 2: "¿Dónde puedo vivir con mi sueldo?" (22/11/2026)
- Hecho B-33: `herramienta_sueldo.py` genera /donde-vivir-con-mi-sueldo/ (calculadora en el navegador + texto y tabla fijos). `generar_web.py` solo la importa, pone la tarjeta en la portada y la añade al sitemap. Test: `tests/test_sueldo.py`.
- Siguiente de la hoja de ruta: comparador de 2 a 4 ciudades (B-35). Después, descarga de datos. El mapa nacional sigue a la espera de confirmar la licencia de la cartografía.

## Sin códigos postales (22/11/2026)
- Decisión de Juan: en la web no aparece ningún código postal; las zonas se nombran por barrios, distritos o algo que se entienda a simple vista. Los distritos sin barrios se nombran por sus núcleos de población o sus dos calles principales (INE), con `etiqueta_zona()` en `preparar_json.py`. El test "Ningún código postal en la web" lo vigila.
- Para mejorar esos 144 distritos (Huelva, Ávila, Toledo, Castellón, San Fernando…) haría falta una lista oficial de barrios de cada ayuntamiento (B-32).

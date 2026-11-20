# CHANGELOG

## 20/11/2026: Barrios de Valladolid en 6 de sus 12 distritos
- Nuevo `zonas_valladolid.py` y `datos_limpios/zonas_nombradas.csv`. `preparar_json.py` y `generar_web.py` leen ese archivo: un distrito sin nombre oficial pero con barrios verificados se muestra como "Distrito 8 · Rondilla, Hospital y otros barrios", con la lista completa y el código postal debajo y la cita del Ayuntamiento bajo la tabla.
- Valladolid: distritos 3, 6, 8, 10, 11 y 12 con barrios (las zonas estadísticas suman exactamente su población); el resto, con código postal y calles.
- Tests: 19 OK, 0 FALLA.

## 20/11/2026: Distritos sin nombre identificados por código postal y calles (B-27)
- Nuevo paso `preparar_zonas.py` (paso 3 de `actualizar.py`, antes de preparar_json): lee el Callejero del Censo Electoral del INE (julio de 2026) y escribe `datos_limpios/zonas_distritos.csv`.
- Los 785 distritos sin nombre oficial pasan de "Distrito 8" a "Distrito 8 · CP 47010 y 47011", con una segunda línea en la tabla: "Calles principales: Portillo de Balboa, Cardenal Torquemada, Moradas" (y "Incluye …" si hay núcleos como La Overuela o Puente Duero). El texto de la ficha, las listas y el mapa usan la misma etiqueta. Nota de fuente y fecha bajo la tabla.
- `tests/test_distritos.py`: todo distrito sin nombre lleva código postal y ninguna tabla muestra solo "Distrito N". `ejecutar_tests.py`: 18 OK, 0 FALLA.

## 20/11/2026: Nombres de distrito de Bilbao y script de verificación (B-23, B-12)
- Nuevo `verificar_distritos.py`: compara las secciones censales de un fichero municipal (en `datos_municipales/`) con las del ADRH del INE y, solo si coinciden todas, escribe los nombres con su fuente en `datos_limpios/nombres_distritos.csv` (`--escribir --fuente "..."`). La primera vez crea `datos_limpios/secciones_adrh_2024.csv` (caché, fuera de git); después tarda unos segundos.
- Bilbao: 8 distritos con nombre oficial (Bilbao Open Data, CC BY 3.0 ES). Las 278 secciones coinciden con el INE. Distritos con nombre en la web: 58 (antes 50).
- Sevilla y Zaragoza buscadas sin encontrar un fichero válido (ver FUENTES.md).
- B-26: nueva columna `cita` en `nombres_distritos.csv`; `preparar_json.py` la pasa al JSON y la ficha muestra "Nombres de los distritos: …" bajo la tabla (Barcelona y Bilbao). Madrid y Valencia no la muestran hasta documentar su fuente (B-20). Nuevo `tests/test_distritos.py`.
- Tests: 18 OK, 0 FALLA, 0 PENDIENTE.

## 20/11/2026: Texto explicativo en cada ficha de ciudad (B-17, en parte)
- Nuevo `textos_ciudad.py`: genera la sección "Qué dicen los datos de <ciudad>" (6-7 párrafos, unas 300 palabras) solo con los datos del JSON, sin estimaciones. Si falta un dato, la frase no se escribe. Compara cada ciudad con la mediana de las ciudades de la web (alquiler, €/m², renta, peso del alquiler, edad media, hogares unipersonales, pisos alquilados por 1.000 habitantes), explica el cambio 2023-2024 y si está entre las 10 que más o menos suben, el rango p25-p75 de €/m², su puesto dentro de la provincia y el distrito más caro y más barato.
- `generar_web.py` solo llama a `seccion_claves()` desde la plantilla de ciudad (y añade "Claves" al menú de la ficha). Las ciudades que se añadan al JSON tienen su texto automáticamente.
- Nuevo `tests/test_textos.py` (8 comprobaciones: sección en todas las fichas, mínimo 5 párrafos y 150 palabras, ningún párrafo repetido entre ciudades, cifras iguales que el JSON, mediana correcta, valores de referencia y sentido de la subida). `ejecutar_tests.py`: 17 OK, 0 FALLA, 0 PENDIENTE.
- Visto en Chromium (escritorio 1280 px y móvil 390 px): sin scroll horizontal.

## 20/11/2026: web publicada
- https://ciudadesendatos.es responde con HTTPS desde GitHub Pages; http y www redirigen a la dirección principal. Comprobados la portada, el sitemap, el canonical y el alquiler de Madrid (868,75 €).

## 19/11/2026: Páginas por comunidad autónoma (B-18)
- Nuevo paso del pipeline `preparar_comunidades.py` (entre preparar_json y generar_web; ya incluido en `actualizar.py`): lee la hoja CCAA del SERPAVI y escribe `datos_limpios/comunidades.json` con el alquiler mediano, €/m², percentiles y la serie 2011-2024 de cada comunidad. La relación provincia → comunidad (códigos del INE) se comprueba con el propio fichero: la suma de inmuebles de las provincias coincide con el total de la comunidad en los 243 pares comunidad-año.
- Nueva página `/comunidades/` (tabla de las 17 comunidades y Ceuta y Melilla: alquiler, €/m², cambio desde 2019 y sus ciudades) y 13 páginas `/comunidades/<nombre>/` para las comunidades con 3 o más ciudades: tabla ordenable de sus ciudades (alquiler, €/m², cambio desde 2019, renta, peso del alquiler), gráfico de evolución, aviso turístico en las de costa, enlaces a las demás y metodología. Aragón, Cantabria, Navarra, La Rioja, Ceuta y Melilla no tienen página propia (menos de 3 ciudades): la tabla enlaza directamente a sus ciudades.
- Fichas de ciudad: miga de pan visible (Inicio › Comunidad › Ciudad) y en JSON-LD, y una frase que compara su alquiler con el de toda su comunidad, con enlace. Portada: bloque "Por comunidad autónoma". Menú: enlace "Comunidades" en todas las páginas.
- Sitemap: 170 URL (antes 156).
- Nuevo `tests/test_comunidades.py` (8 comprobaciones: valores de referencia por comunidad, una página por comunidad con exactamente sus ciudades, migas de pan, comparación en cada ficha, índice y sitemap completo). `ejecutar_tests.py`: 16 OK, 0 FALLA, 0 PENDIENTE.
- Prueba en Chromium (escritorio 1280 px y móvil 390 px): sin scroll horizontal, tablas ordenables y sin errores de JavaScript, 20 de 20 OK. Firefox, Safari y móvil real siguen sin probar (B-14).

## 19/11/2026: Preparada la publicación en ciudadesendatos.es (B-03, Fase 1)
- Juan compró el dominio ciudadesendatos.es (DonDominio, sin hosting). Se publica con GitHub Pages.
- `generar_web.py`: BASE_URL = https://ciudadesendatos.es. Con ello se activan sitemap.xml (156 URL), la línea Sitemap en robots.txt, canonical, og:url, og:image y la miga de pan en JSON-LD. Escribe también `web/CNAME`.
- Nuevo `.github/workflows/publicar.yml`: cada vez que se sube a main un cambio en web/, GitHub Actions publica esa carpeta en Pages. La web se sigue generando en el ordenador.
- Tests: 15 OK, 0 FALLA, 0 PENDIENTE (incluye "Con dominio: canonical, og:url y og:image en todas las páginas").
- Pendiente de Juan: crear el repositorio en GitHub, subir el código, activar Pages y poner los registros DNS en DonDominio.

## 19/11/2026: Licencia propia CC BY 4.0 (B-16)
- Decisión de Juan: los datos elaborados y los textos de ciudadesendatos se publican con licencia CC BY 4.0. Los datos de origen mantienen la licencia de sus fuentes.
- El pie de todas las páginas lo indica con enlace (`rel="license"`) y cada Dataset del JSON-LD lleva `license`. Constantes LICENCIA y LICENCIA_URL en `generar_web.py`.
- `tests/test_seo.py` comprueba la licencia en el pie y en los datos estructurados. `ejecutar_tests.py`: 15 OK, 0 FALLA, 0 PENDIENTE.

## 18/11/2026: corrección de los riesgos de la auditoría
- Riesgo 5: nuevo `config.py` con el año, las rutas y los valores de referencia. Los scripts del pipeline (y `generar_web.py`) leen el año de ahí. Nuevo `actualizar.py`, que ejecuta todo y los tests con un solo comando y se para en el primer error. `preparar_json.py` termina con error si los valores de referencia no cuadran. Salida idéntica a la anterior (comprobado por hash).
- Riesgo 2: licencia del SERPAVI confirmada en el aviso legal de mivau.gob.es y URL oficial de descarga registrada en FUENTES.md. La fecha del pie la añadió el hilo de SEO (B-01).
- Riesgo 4: aviso destacado sobre las zonas turísticas en la portada y en los 4 rankings.
- Riesgo 3 (empezado): nombres oficiales de los 10 distritos de Barcelona (Open Data BCN, CC BY 4.0), con los códigos verificados sección a sección frente al INE.
- Tests: detecta variables sin rellenar ({...}) en el texto y exige el aviso turístico. Resultado: 15 OK, 0 FALLA.

## 18/11/2026: Mejoras SEO (auditoría SEO, prioridades 1 a 3)
Hecho (en `generar_web.py`; copia previa en `_copias/2026-11-18/`):
- Títulos de ciudad más cortos (todos ≤ 60 caracteres), con el nombre más usado al buscar (Alicante, Elche, Castellón de la Plana, Ibiza…). El H1 mantiene el nombre oficial del INE. Rankings sin el sufijo de marca.
- La descripción ya no dice "Datos oficiales por distrito" en las 21 ciudades sin desglose. Descripción de los rankings ≤ 160 caracteres.
- Datos estructurados JSON-LD: Dataset en todas las páginas (fuentes, periodo, lugar, fecha), WebSite en la portada y BreadcrumbList (esta solo cuando haya BASE_URL, porque Google pide URL absoluta).
- og:locale y og:site_name siempre; og:url, og:image (1200×630) y twitter:card cuando haya BASE_URL. Sitemap con `<lastmod>`.
- Favicon como archivo (`favicon.png` 48×48 y `favicon.ico`). Imágenes en `recursos/`, creadas con `crear_imagenes.py` (necesita Pillow solo si se quieren rehacer).
- Cada ficha tiene un bloque "X en los rankings" con su puesto en los 4 rankings, enlazado a su fila (`#c-<slug>`).
- B-01: el pie indica la fecha de actualización de cada fuente (SERPAVI 08/07/2026, ADRH 19/10/2026) y la fecha de generación de la página.
- Nuevo `tests/test_seo.py` (11 comprobaciones, incluida una que exige las dos fechas en el pie y ninguna llave sin rellenar). `ejecutar_tests.py`: 13 OK, 0 FALLA, 0 PENDIENTE.


## 18/11/2026: Fase 0, auditoría
Hecho:
- Repositorio git local (rama `main`). Primer commit con el estado anterior a cualquier cambio. `.gitignore` deja fuera `datos_originales/` y los dos intermedios pesados. `.gitattributes` normaliza los saltos de línea.
- Pipeline ejecutado completo (procesar_nacional → unir_nacional → preparar_json → generar_web). Los valores de referencia de Madrid, Valencia y Valladolid son correctos. El resultado es idéntico al anterior, salvo la fecha "generado" del JSON.
- Nuevo `tests/ejecutar_tests.py` con 12 comprobaciones: 10 OK y 2 PENDIENTES conocidas (B-01 fecha de actualización, B-05 títulos largos).
- Prueba en navegador (Chromium sin interfaz, escritorio 1280 px y móvil 390 px): buscador (también sin tildes y con apóstrofo), ordenar tablas, mapa de Madrid, sin scroll horizontal y sin errores de JavaScript. 20 de 20 OK. El script está en `tests/prueba_navegador.js` (necesita Node y Playwright; opcional).
- Licencias comprobadas en la fuente: INE (CC BY 4.0), SEPE paro municipal (CC BY 4.0) y Transacciones inmobiliarias del Ministerio de Vivienda (CC BY 4.0). Registradas en FUENTES.md.
- Nuevos PROYECTO.md, BACKLOG.md, FUENTES.md, CHANGELOG.md e INFORME_FASE0.md.

No se ha cambiado ningún script del pipeline, ningún dato ni la web.

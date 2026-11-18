# CHANGELOG

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

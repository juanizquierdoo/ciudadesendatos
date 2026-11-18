# CHANGELOG

## 18/11/2026: Fase 0, auditoría
Hecho:
- Repositorio git local (rama `main`). Primer commit con el estado anterior a cualquier cambio. `.gitignore` deja fuera `datos_originales/` y los dos intermedios pesados. `.gitattributes` normaliza los saltos de línea.
- Pipeline ejecutado completo (procesar_nacional → unir_nacional → preparar_json → generar_web). Los valores de referencia de Madrid, Valencia y Valladolid son correctos. El resultado es idéntico al anterior, salvo la fecha "generado" del JSON.
- Nuevo `tests/ejecutar_tests.py` con 12 comprobaciones: 10 OK y 2 PENDIENTES conocidas (B-01 fecha de actualización, B-05 títulos largos).
- Prueba en navegador (Chromium sin interfaz, escritorio 1280 px y móvil 390 px): buscador (también sin tildes y con apóstrofo), ordenar tablas, mapa de Madrid, sin scroll horizontal y sin errores de JavaScript. 20 de 20 OK. El script está en `tests/prueba_navegador.js` (necesita Node y Playwright; opcional).
- Licencias comprobadas en la fuente: INE (CC BY 4.0), SEPE paro municipal (CC BY 4.0) y Transacciones inmobiliarias del Ministerio de Vivienda (CC BY 4.0). Registradas en FUENTES.md.
- Nuevos PROYECTO.md, BACKLOG.md, FUENTES.md, CHANGELOG.md e INFORME_FASE0.md.

No se ha cambiado ningún script del pipeline, ningún dato ni la web.

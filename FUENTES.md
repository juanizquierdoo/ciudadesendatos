# FUENTES

Registro de cada fuente de datos: qué es, nivel territorial, fecha, licencia y cómo se cita.
Regla: un dato no entra en la web sin una fila aquí con la licencia **leída en la fuente**.
"Verificado" indica la fecha en la que se leyó la licencia y dónde.

## En uso

### 1. Alquiler: SERPAVI (Ministerio de Vivienda y Agenda Urbana)
- **Archivo:** `datos_originales/Datos_municipios_2024.xlsx` (BD SERPAVI 2011-2024, "DEFINITIVO WEB_v2").
- **Qué mide:** alquiler de vivienda habitual declarado en el IRPF (Modelo 100), sin alquileres a familiares. Medianas y percentiles 25 y 75 del alquiler mensual (€ y €/m²), superficie y número de inmuebles. Usamos solo vivienda colectiva (pisos, sufijo `_VC`).
- **Niveles:** CCAA, provincia, municipio, distrito y sección censal. Usa los códigos del **Censo 2021** del INE.
- **Periodo:** 2011-2024. Metadatos corregidos el 08/07/2026 (según la hoja "Metadatos").
- **Licencia:** INSTRUCCIONES_PROYECTO.md la da por revisada: reutilización permitida, también comercial. **Falta registrar la URL oficial (B-02).** Aviso: el PDF `SERPAVI2026...pdf` dice "Todos los derechos reservados", pero se refiere a la publicación en PDF. En datos.gob.es, otro conjunto del mismo ministerio ("Transacciones inmobiliarias de vivienda") figura como CC BY 4.0 (leído el 18/11/2026). Eso es un indicio, no una confirmación para el SERPAVI.
- **Cita que usamos:** "Origen de los datos: Ministerio de Vivienda y Agenda Urbana (SERPAVI, datos de 2024)".
- **Condiciones:** indicar la fecha (pendiente, B-01), no desnaturalizar el sentido de los datos, no sugerir patrocinio y no usar sus logotipos.

### 2. Renta: Atlas de Distribución de Renta de los Hogares (ADRH), INE
- **Archivo:** `datos_originales/renta_total.csv` (392 MB) y los CSV por ciudad.
- **Qué mide:** renta neta media por hogar y por persona, mediana por unidad de consumo y renta bruta. Procede de datos tributarios (AEAT, Haciendas Forales).
- **Niveles:** sección censal, distrito, municipio, provincia y CCAA.
- **Periodo:** usamos 2024 (definitivo, nota de prensa del 19/10/2026) y la serie 2015-2024.
- **Licencia:** **CC BY 4.0**, verificado el 18/11/2026 en el Aviso legal del INE (https://ine.es/dyngs/AYU/es/index.htm?cid=125): "Creative Commons Reconocimiento 4.0 (CC BY 4.0)", "salvo que se indique lo contrario". Permite el uso comercial.
  - Aviso: el pie de página de ine.es dice "CC BY-SA 4.0", pero enlaza a CC BY 4.0. Nos guiamos por el Aviso legal, que es el documento específico. `fuentes.txt` decía BY-SA: está desactualizado y lo sustituye este archivo.
- **Cita que usamos:** "Elaboración propia con datos extraídos del sitio web del INE: www.ine.es" (es la fórmula que sugiere el Aviso legal cuando hay tratamiento de los datos).
- **Condiciones:** mencionar la fecha de actualización si figura en el original (pendiente, B-01) y no sugerir que el INE participa, patrocina o apoya la web.

### 3. Demografía: indicadores demográficos del ADRH, INE
- **Archivo:** `datos_originales/demograficos_total.csv` (446 MB).
- **Qué mide:** población, edad media, % de menores de 18 y de mayores de 65, % de población española, tamaño medio del hogar y % de hogares unipersonales.
- **Nivel y periodo:** usamos el municipio, año 2024.
- **Licencia y cita:** las mismas que la fuente 2 (INE, CC BY 4.0).

## Candidatas comprobadas (todavía sin usar)
| Fuente | Publicador | Nivel | Periodicidad | Licencia (dónde se leyó, 18/11/2026) | Pendiente de verificar |
|---|---|---|---|---|---|
| Paro registrado por municipio | SEPE | Municipio, por sexo, edad y sector | Ficheros anuales en CSV y semestrales en XLS; última actualización de la distribución: 19/06/2026 | CC BY 4.0 (ficha de datos.gob.es: ea0041513-paro-registrado-por-municipio) | Qué años cubre exactamente; denominador para calcular una tasa (el paro registrado no es la tasa de paro de la EPA) |
| Transacciones inmobiliarias de vivienda | Ministerio de Vivienda y Agenda Urbana | "Por ámbito geográfico", sin concretar | Trimestral; CSV `VDP003_01.csv` | CC BY 4.0 (ficha de datos.gob.es: e05233601-transacciones-inmobiliarias-de-vivienda) | **Nivel territorial**: hay que abrir el CSV y su readme para ver si llega a municipio |
| Valor tasado de la vivienda libre (municipios de más de 25.000 hab.) | Ministerio (según el título) | Municipio de más de 25.000 hab. (según el título) | No consta | **No consta** en la ficha de datos.gob.es (casi vacía) | Todo: publicador, licencia, formato y periodo |
| Viviendas de uso turístico (estadística experimental) | INE | Ofrece mapas municipales; no consta si hay sección censal | Dos veces al año (mayo y noviembre desde el segundo semestre de 2024) | Aviso legal del INE (CC BY 4.0); la página no indica otra licencia | Último periodo publicado; formato de descarga; carácter experimental (hay que avisarlo) |
| Cartografía de secciones censales | INE | Sección censal (en SHAPE, UTM huso 30) | Ficheros anuales de 2001 a 2026 (falta 2002); también WMS, WFS y API Features | La página no da una licencia propia; el Aviso legal del INE habla de "información estadística" y no menciona la cartografía | Si la cartografía está bajo CC BY 4.0; si trae distritos o hay que agregarlos desde las secciones |
| Datos de datos.gob.es en general | Varios | | | Condiciones generales: permiten uso comercial; obligan a citar, indicar la fecha y no desnaturalizar los datos (aviso legal de datos.gob.es). La licencia concreta va en cada ficha | |

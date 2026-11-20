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
- **Descarga oficial:** https://www.mivau.gob.es/vivienda/alquila-bien-es-tu-derecho/serpavi → "BD Sistema Estatal Índices de Alquiler de Vivienda (Xlsx)", archivo `2026-03_09_bd_SERPAVI_2011-2024 - DEFINITIVO WEB_v2.xlsx` en cdn.mivau.gob.es (comprobado el 18/11/2026).
- **Licencia:** verificada el 18/11/2026 en el aviso legal del Ministerio (https://www.mivau.gob.es/ministerio/aviso-legal), que se aplica al portal "y todos los Subdominios y Directorios". Dice que la información "es susceptible de reutilización" y que está autorizada su reproducción, modificación y distribución "para usos comerciales y no comerciales", salvo indicación expresa en contrario. Remite a las condiciones generales de datos.gob.es/avisolegal (Ley 37/2007 y RD 1495/2011).
  - Condiciones: no desnaturalizar el sentido de la información; citar la fuente (fórmula sugerida: "Origen de los datos: Ministerio de Vivienda y Agenda Urbana"); mencionar la fecha de la última actualización; no sugerir que el Ministerio participa, patrocina o apoya la web; conservar los metadatos de fecha y de condiciones de reutilización. Los logotipos y las marcas están protegidos: no se usan.
  - Excepción: el PDF `SERPAVI2026...pdf` dice expresamente "Todos los derechos reservados". Es una indicación en contrario para ese PDF, así que **el PDF no se reproduce**. La base de datos en Excel no lleva esa mención.
  - El aviso legal de la sede electrónica (mivau.sede.gob.es) es más restrictivo, pero se refiere a la sede, no al portal desde el que se descarga el SERPAVI.
- **Cita que usamos:** "Origen de los datos: Ministerio de Vivienda y Agenda Urbana (SERPAVI, datos de 2024)".
- **Nivel comunidad autónoma (desde 19/11/2026):** hoja "CCAA" del mismo fichero, columnas de vivienda colectiva (`ALQTBID12_M_VC`, `ALQM2_LV_*_VC`, `BI_ALVHEPCO_TVC`). Misma licencia y cita. Navarra tiene serie desde 2021 y el País Vasco solo 2024 (régimen foral). La relación provincia → comunidad usa los códigos del INE que trae el propio fichero y se comprueba sumando los inmuebles de las provincias (`preparar_comunidades.py`).
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

### 4. Nombres de distrito
- `datos_limpios/nombres_distritos.csv` (columnas: codigo, nombre_distrito, fuente). Se edita a mano; cada fila lleva su fuente.
- **Barcelona (10 distritos):** Ajuntament de Barcelona, Open Data BCN, conjunto "20170706-districtes-barris", **CC BY 4.0** (según el portal, consultado el 18/11/2026). Cita: "Ajuntament de Barcelona, Open Data BCN". Verificación: el fichero municipal de secciones censales tiene las mismas 1068 secciones (distrito + sección) que el ADRH 2024 del INE, así que los códigos de distrito coinciden. Los nombres son los oficiales en catalán.
- **Bilbao (8 distritos, desde 20/11/2026):** Ayuntamiento de Bilbao, Bilbao Open Data, conjunto "Distritos y secciones estadísticas de Bilbao 2022" (https://www.bilbao.eus/bilbaoopendata/demografia/distritos_secciones_2022.csv; ficha en datos.gob.es l01480209-distritos-y-secciones-estadisticas-de-bilbao-2022). Copia en `datos_municipales/48020_bilbao_secciones_2022.csv` (mismo contenido, en UTF-8 y con distrito y sección a 2 y 3 cifras).
  - **Licencia:** **CC BY 3.0 ES**, leída el 20/11/2026 en https://www.bilbao.eus/opendata/es/licencia-para-conjunto-de-datos ("si no se indica lo contrario"). Condiciones: no alterar el contenido, no desnaturalizar su sentido, citar la fuente y mencionar la fecha de la última actualización. Cita que piden (https://www.bilbao.eus/opendata/es/reconocimiento): "Fuente de los datos: Ayuntamiento de Bilbao".
  - **Verificación:** con `verificar_distritos.py`, las 278 secciones (distrito + sección) del fichero de 2022 coinciden exactamente con las del ADRH 2024 del INE. El fichero de 2023 del mismo portal tiene solo 273 (le faltan 5 secciones que sí están en el INE y en el de 2022), así que se usa el de 2022.
  - Nombres en euskera, tal como los publica el Ayuntamiento (Deustu, Uribarri, Otxarkoaga-Txurdinaga, Begoña, Ibaiondo, Abando, Errekalde, Basurtu-Zorrotza); solo se pasan de MAYÚSCULAS a mayúscula inicial.
- **Buscadas sin éxito (20/11/2026):** Sevilla (no se encontró un fichero municipal de secciones con su distrito), Zaragoza (sus distritos municipales no son los distritos censales del INE; hay datos por sección en zaragoza.es, pero sin el distrito censal). Pendientes: Córdoba, Murcia, Palma, Las Palmas, Alicante, Vigo, Gijón, Vitoria, A Coruña, Granada.
- **Madrid y Valencia:** incorporados antes de la Fase 0, con la fuente sin documentar (B-20).
- Método para añadir una ciudad: (1) buscar en el portal de datos abiertos del ayuntamiento un fichero de secciones censales con su distrito y anotar su licencia; (2) comprobar que el conjunto (distrito, sección) es idéntico al del ADRH del INE; (3) solo si coincide, añadir los nombres con su fuente. Si no coincide (por ejemplo, porque los distritos municipales no son los censales), no se añade.

## Candidatas comprobadas (todavía sin usar)
| Fuente | Publicador | Nivel | Periodicidad | Licencia (dónde se leyó, 18/11/2026) | Pendiente de verificar |
|---|---|---|---|---|---|
| Paro registrado por municipio | SEPE | Municipio, por sexo, edad y sector | Ficheros anuales en CSV y semestrales en XLS; última actualización de la distribución: 19/06/2026 | CC BY 4.0 (ficha de datos.gob.es: ea0041513-paro-registrado-por-municipio) | Qué años cubre exactamente; denominador para calcular una tasa (el paro registrado no es la tasa de paro de la EPA) |
| Transacciones inmobiliarias de vivienda | Ministerio de Vivienda y Agenda Urbana | "Por ámbito geográfico", sin concretar | Trimestral; CSV `VDP003_01.csv` | CC BY 4.0 (ficha de datos.gob.es: e05233601-transacciones-inmobiliarias-de-vivienda) | **Nivel territorial**: hay que abrir el CSV y su readme para ver si llega a municipio |
| Valor tasado de la vivienda libre (municipios de más de 25.000 hab.) | Ministerio (según el título) | Municipio de más de 25.000 hab. (según el título) | No consta | **No consta** en la ficha de datos.gob.es (casi vacía) | Todo: publicador, licencia, formato y periodo |
| Viviendas de uso turístico (estadística experimental) | INE | Ofrece mapas municipales; no consta si hay sección censal | Dos veces al año (mayo y noviembre desde el segundo semestre de 2024) | Aviso legal del INE (CC BY 4.0); la página no indica otra licencia | Último periodo publicado; formato de descarga; carácter experimental (hay que avisarlo) |
| Cartografía de distritos y secciones censales para el SERPAVI | Ministerio de Vivienda y Agenda Urbana | Distrito y sección censal (zip en la página del SERPAVI) | Según el nombre del archivo, los distritos son de 2011 y las secciones de 2021 | Aviso legal de mivau.gob.es (reutilización comercial permitida) | Si los límites de 2011 sirven para los distritos de 2024 |
| Cartografía de secciones censales | INE | Sección censal (en SHAPE, UTM huso 30) | Ficheros anuales de 2001 a 2026 (falta 2002); también WMS, WFS y API Features | La página no da una licencia propia; el Aviso legal del INE habla de "información estadística" y no menciona la cartografía | Si la cartografía está bajo CC BY 4.0; si trae distritos o hay que agregarlos desde las secciones |
| Datos de datos.gob.es en general | Varios | | | Condiciones generales: permiten uso comercial; obligan a citar, indicar la fecha y no desnaturalizar los datos (aviso legal de datos.gob.es). La licencia concreta va en cada ficha | |

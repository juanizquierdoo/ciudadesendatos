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
- **Buscadas sin éxito (20/11/2026):**
  - Sevilla: no se encontró un fichero municipal de secciones con el nombre de su distrito (solo anuarios en PDF).
  - Zaragoza: hay datos por sección censal en zaragoza.es, pero sin el nombre del distrito; sus juntas de distrito no coinciden con los 12 distritos del INE.
  - Palma: solo los "Districtes censals 2017" del Govern balear (catálogo CAIB), sin nombres municipales.
  - Las Palmas de Gran Canaria: el portal municipal solo tiene el callejero.
  - A Coruña: datos.coruna.gal tiene los distritos y secciones censales, pero solo como servicio de mapas (ArcGIS/WMS, 2021) y sin nombres; no se ha comprobado si el servicio trae alguno.
  - Vitoria-Gasteiz: solo PDF y tablas de Eustat.
  - Valladolid: sus 12 distritos son divisiones estadísticas sin nombre oficial (INSTRUCCIONES_PROYECTO.md).
- Sin buscar todavía: Córdoba, Murcia, Alicante, Vigo, Gijón, Granada y el resto.
- **Madrid y Valencia:** incorporados antes de la Fase 0, con la fuente sin documentar (B-20).
- Método para añadir una ciudad: (1) buscar en el portal de datos abiertos del ayuntamiento un fichero de secciones censales con su distrito y anotar su licencia; (2) comprobar que el conjunto (distrito, sección) es idéntico al del ADRH del INE; (3) solo si coincide, añadir los nombres con su fuente. Si no coincide (por ejemplo, porque los distritos municipales no son los censales), no se añade.

### 5. Zonas de los distritos sin nombre: Callejero del Censo Electoral, INE (desde 20/11/2026)
- **Archivo:** `datos_originales/caj_esp_072026/` (ficheros TRAM y VIAS; nacional, publicación de julio de 2026, situación a 30/06/2026), descargado de https://www.ine.es/dyngs/DAB/es/index.htm?cid=1390 (`caj_esp_072026.zip`, 50 MB). Diseño de registro: `datos_originales/Dis_nuevo.xlsx` (el bloque de la situación actual empieza en la posición 71).
- **Qué da:** cada tramo de calle con su sección censal y su código postal ("distrito postal de cada tramo", según la página del INE), y la unidad poblacional (núcleo).
- **Uso:** `preparar_zonas.py` describe cada distrito con los códigos postales presentes en al menos el 20 % de sus secciones, las 3 calles que pasan por más secciones y los núcleos distintos del principal. Solo se muestra en los distritos **sin nombre oficial** (785 de 864). Los nombres de calle van como los da el INE (sin tildes y, en algunas ciudades como Bilbao, con el apellido delante); solo se cambian mayúsculas y "(EL)" → "El".
- **Ojo:** el callejero es de 2026 y el ADRH de 2024. Los códigos de distrito son los mismos, pero algunas secciones han cambiado (Valladolid: 256 secciones en 2026 frente a 266 en 2024). Para describir la zona del distrito basta.
- **Licencia:** INE, CC BY 4.0 (Aviso legal, ver fuente 2). Cita: la general del INE del pie, y en la ficha se indica la fecha del callejero.

### 6. Barrios de los distritos de Valladolid (desde 20/11/2026)
- **Archivos** (en `datos_municipales/`, descargados por Juan de valladolid.es, Observatorio Urbano): población por zonas estadísticas 1986-2025 y por distritos 1981-2025 (actualizados el 13/07/2026), documentos de delimitación de los distritos censales y de las zonas estadísticas. También está el Excel de las elecciones generales de 2023 por distritos y zonas, que no se usa porque no relaciona zonas con distritos.
- **Licencia:** portal Open Data del Ayuntamiento de Valladolid: "si no se indica lo contrario", **CC BY 3.0 ES** (leído el 20/11/2026 en https://www.valladolid.es/es/temas/hacemos/open-data-datos-abiertos).
- **Verificación** (`zonas_valladolid.py`): los 12 distritos municipales son los distritos censales del INE (el documento los titula así y la población de cada uno coincide con el ADRH 2024 con diferencias de 0-4 %). Las zonas estadísticas no siempre caben enteras en un distrito. Se acepta un distrito solo si la suma de la población de sus zonas coincide **exactamente** con la del distrito; ocurre en los distritos 3, 6, 8, 10, 11 y 12, y en cuatro fechas distintas (2021, 2024, 2025 y julio de 2026). Los distritos 1, 2, 4, 5, 7 y 9 tienen zonas repartidas (Centro, Universidad, Campo Grande...) y se quedan con código postal y calles.
- Resultado en `datos_limpios/zonas_nombradas.csv` (codigo, zonas, fuente, cita), formato compartido con el hilo de barrios de otras ciudades.

### 6. Barrios de los distritos sin nombre oficial: otras ciudades (desde 20/11/2026)
Script: `zonas_ciudades.py` → `datos_limpios/zonas_nombradas.csv` (columnas codigo, zonas, fuente, cita, nota; Valladolid lo escribe `zonas_valladolid.py`). Cada script solo toca las filas de sus municipios. La columna `nota` explica en la ficha cómo se asignaron los barrios.
- **Sevilla (11 distritos):** capa "Barrios" de ide.SEVILLA (Ayuntamiento de Sevilla, Gerencia de Urbanismo; ArcGIS item 38827fc3eac142149801c2efa2a0bdf9, servicio `services1.arcgis.com/hcmP7kr0Cx3AcTJk/arcgis/rest/services/Barrios_de_Sevilla/FeatureServer`), 110 barrios con número y nombre de distrito, actualizada el 12/06/2024. **Licencia: CC BY 4.0** (leída en la ficha del conjunto en cda-idesevilla.opendata.arcgis.com, 20/11/2026; el portal ide.SEVILLA figura en datos.gob.es con CC0). Copia: `datos_municipales/41091_sevilla_barrios_por_distrito.csv`.
  - **Verificación:** población por distrito del Anuario Estadístico de la ciudad de Sevilla 2023 (tabla 1.1.3, padrón a 1/1/2024; `datos_municipales/41091_sevilla_poblacion_distritos_2024.csv`) frente al ADRH 2024: los 11 distritos van en el mismo orden y difieren entre el −1,0 % y el −2,7 %, salvo Casco Antiguo (−6,7 %). Los códigos postales del callejero del INE también cuadran (41001-41003 en el distrito 1, 41010 en Triana…). No hay fichero municipal de secciones, así que no es la verificación sección a sección de Barcelona y Bilbao: por eso los nombres van como "barrios" y no en nombres_distritos.csv.
- **Zaragoza (12 distritos):** IDEZar (Ayuntamiento de Zaragoza), capas `urbanismo:Juntas_Municipales_Vecinales` (30 juntas) y `ctsvg:ISV_Secciones_Censales_2024` (501 secciones con población), API OGC de idezar-sig.zaragoza.es, consultadas el 20/11/2026. **Licencia:** Aviso legal de zaragoza.es, "Condiciones generales para la reutilización": permite uso comercial; obliga a no desnaturalizar, citar ("Origen de los datos: Ayuntamiento de Zaragoza") y fechar.
  - **Método (cruce propio):** cada sección va a la junta que contiene su centro; resumen en `datos_municipales/50297_zaragoza_juntas_por_distrito_censal.csv`. Se nombra una junta si reúne ≥10 % de la población del distrito y, en distritos de 10 o más secciones, al menos 2 secciones (así se descartó Alfocea, cuya única sección es sobre todo Monzalbarba según el callejero del INE). La población del distrito así sumada difiere del ADRH 2024 entre +1 % y +7 %. El Ayuntamiento tiene 501 secciones y el ADRH 2024, 510.
- **Málaga (publicado desde el 20/11/2026):** datosabiertos.malaga.eu, "Sistema de Información Cartográfica - Barrio" (419 barrios) y "- Sección Censal" (441 secciones), actualizados el 19/11/2026. Cruce propio sección → barrio en `datos_municipales/29067_malaga_barrio_por_seccion_censal.csv`, ponderado con la población del ADRH 2024 (`datos_limpios/poblacion_secciones_adrh_2024.csv`). **Licencia dudosa:** el título dice CC BY 4.0 y la licencia del conjunto es CC BY-SA 4.0 (`license_id` by-sa-40). Juan aceptó el 20/11/2026 usarlo como CC BY-SA 4.0: la lista de barrios de Málaga se publica con esa licencia (lo dice la nota bajo su tabla) y el resto de la web sigue en CC BY 4.0. No es asesoramiento legal.
- **Tanda 2, buscadas el 20/11/2026 sin una fuente que se pueda usar todavía:**
  - Las Palmas de Gran Canaria: el Ayuntamiento publica barrios (122, con su distrito municipal), distritos y secciones censales (sit.laspalmasgc.es/server/rest/services/opendata), pero las secciones no traen el código de distrito ni se puede descargar su geometría; el número de distrito de los barrios no siempre es el del INE (La Isleta: distrito municipal 2, pero sus calles están en la sección 03040 del INE). La ficha de datos.gob.es no indica licencia. Posible, pero haría falta otro método.
  - Granada: la IDE municipal (granada.org/intranet/idegeogr.nsf) tiene secciones censales por año y tablas de población por Junta Municipal de Distrito y Asociación de Vecinos, pero esas tablas se calculan por interpolación, sin una tabla sección → distrito; los distritos municipales solo están en PDF. Sin licencia indicada.
  - Vigo: datos.vigo.org tiene el callejero con números de portal y coordenadas, pero ninguna capa de barrios.
  - Gijón: población por barrios y parroquias (padrón 2012) y consejos de distrito, sin relación con las secciones censales.
  - Murcia, Palma, Córdoba y Alicante: no se encontró en sus portales ni en datos.gob.es una capa de barrios con licencia y relacionable con las secciones censales. En ArcGIS Online hay capas de barrios de Murcia y Palma subidas por usuarios sin licencia indicada: no se usan.
  - Estas ciudades siguen con código postal, calles principales y núcleos (fuente 5).

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

# CHANGELOG

## 23/11/2026: mapa de distritos con escala de color fija y etiqueta (petición de Juan)
- La escala de color es la misma en todas las ciudades (antes iba del mínimo al máximo de cada ciudad, y una ciudad barata podía parecer cara). Rangos fijos en `ESCALA_MAPA` (`generar_web.py`): peso del alquiler 10-25 %, alquiler 300-1.100 €/mes, renta del hogar 20.000-80.000 €/año, elegidos con los 677 distritos con mapa (del percentil 2 al 98 aprox.). Lo que queda fuera toma el color del extremo; la barra lo indica con ≤ y ≥.
- Encima de la barra se dice qué se mide: "Alquiler sobre renta del hogar (%)", "Alquiler mediano al mes (€)" o "Renta neta media del hogar (€ al año)". Nota bajo el mapa: "Los colores usan la misma escala en todas las ciudades".
- `tests/test_mapa.py`: nueva comprobación (6 OK). `ejecutar_tests.py`: 23 OK. Probado en Chromium (1280 y 390 px) en 14 ciudades, sin errores de JavaScript.

## 23/11/2026: mapa de distritos en 88 ciudades (petición de Juan)
- Antes solo Madrid tenía el mapa esquemático (casillas coloreadas por peso del alquiler, alquiler o renta). Ahora lo tienen las 88 ciudades con 5 distritos o más cuya posición se puede calcular: entre ellas Barcelona, Valencia, Sevilla, Málaga, Bilbao, Vitoria, Donostia, Vigo, A Coruña, Santiago, Lugo, Pontevedra, Oviedo y Gijón.
- Nuevo paso del pipeline `mapa_distritos.py` (ya en `actualizar.py`, antes de `generar_web.py`): calcula el centro de cada distrito con el callejero del INE y las calles y parroquias de OpenStreetMap, y lo pasa a una rejilla. Escribe `datos_limpios/mapa_distritos.csv`. Método y cita en FUENTES.md (fuente 8). Madrid conserva su colocación hecha a mano.
- `generar_web.py`: lee ese CSV (antes, posiciones de Madrid escritas en el código); el mapa incluye también los distritos con pocos datos (con * y aviso) y los de menos de 30 inmuebles (en gris, solo con la renta), igual que la tabla. Ancho de la rejilla según la ciudad, nombres largos recortados en la casilla (enteros en el panel) y cita de OpenStreetMap bajo el mapa.
- Sin mapa: Zaragoza, Valladolid y Las Palmas (faltan sus calles de OSM), San Fernando y Ferrol (un distrito sin calles suficientes) y 37 ciudades con menos de 5 distritos.
- Nuevo `tests/test_mapa.py` (5 comprobaciones). `ejecutar_tests.py`: 23 OK, 0 FALLA. Probado en Chromium (1280 px y 390 px) en 14 ciudades: casillas, panel, cambio de color, sin scroll horizontal y sin errores de JavaScript.

## 22/11/2026: el buscador de la portada muestra primero las ciudades (petición de Juan)
- Antes, al escribir "Madrid" debajo de la caja solo salían barrios (Puerta de Madrid, Colònia Madrid); la ciudad solo aparecía filtrada en "Todas las ciudades", mucho más abajo.
- Ahora salen primero hasta 5 ciudades que coinciden (las que empiezan por lo escrito, antes), desde 2 letras, y después los barrios. Con Enter se abre el primer resultado.
- `generar_web.py`: JavaScript del buscador y una regla de CSS. `ejecutar_tests.py`: 22 OK. Probado en Chromium ("Madrid", "va", "triana", "sevilla"), sin errores de JavaScript.

## 22/11/2026: "Todas las ciudades" plegada con botón «Ver las 151 ciudades» (petición de Juan)
- En la portada solo se ven 4 filas de la lista (12 ciudades en ordenador, 8 en tableta, 5 en móvil) y un botón «Ver las 151 ciudades ▾» / «Ver menos ▴» que despliega el resto.
- Sin JavaScript: casilla oculta + CSS, así que funciona aunque el JavaScript falle. Los 151 enlaces siguen en el HTML (Google los ve igual). Al escribir en el buscador se muestran todas las coincidencias y el botón se oculta.
- `generar_web.py`: HTML de la sección, unas reglas de CSS y una línea en el JavaScript del buscador. `ejecutar_tests.py`: 22 OK, 0 FALLA.
- Probado en Chromium a 1400 px, 800 px y 390 px (iPhone 13), también con el móvil en modo oscuro (la web se ve en claro, como el resto): plegar, desplegar, volver a plegar, buscar, borrar la búsqueda y abrir con teclado.

## 22/11/2026: comparador de 2 a 4 ciudades (Fase 2, funcionalidad 2, B-35)
- Nuevo `comparador_ciudades.py`: página /comparar-ciudades/. Eliges de 2 a 4 ciudades (desplegables por comunidad) y salen lado a lado: alquiler mediano, €/m² con su rango p25-p75, superficie, alquiler sobre la renta, ingresos para la regla del 30 %, cambio del alquiler 2019-2024 y 2023-2024, renta por hogar y por persona y su cambio, población, edad, menores de 18, mayores de 65, hogares unipersonales, tamaño del hogar, distritos con dato y el distrito más barato y el más caro (con enlace a su fila de la ficha). Encima, frases con las diferencias principales; debajo, gráfico de la evolución del alquiler 2011-2024.
- Solo datos que ya estaban en ciudades_nivel1.json; los cálculos son los mismos que los rankings y la calculadora del sueldo. Distritos con la regla de la ficha (menos de 30 inmuebles no se usan; 30-99 con *) y sin códigos postales. El cálculo se hace en el navegador; la dirección guarda las ciudades (?c=valladolid,salamanca) para compartir, y hay botón «Copiar enlace».
- Una sola página, sin páginas por pareja de ciudades (serían miles casi iguales, regla 8). Sin JavaScript (y para Google) se ve la comparación de las 4 ciudades más pobladas, calculada en Python con las mismas reglas, más un texto «Qué dicen los datos al comparar» y 6 comparaciones de ejemplo.
- `generar_web.py`: 4 líneas (import, tarjeta en la portada, enlace «Compara X lado a lado con otras ciudades» en la sección «Compara con otras ciudades» de cada ficha y llamada en main() que añade la URL al sitemap).
- Nuevo `tests/test_comparador.py` (8 comprobaciones). `ejecutar_tests.py`: 22 OK, 0 FALLA.
- Probado en Chromium (1280 px y 390 px): carga, cambio de ciudades, ciudad repetida, enlaces con parámetros (también inválidos), enlace desde la ficha, enlace a distrito, sin scroll horizontal de página, sin errores de JavaScript, y la tabla que pinta el JavaScript es idéntica a la fija. Firefox, Safari y móvil real sin probar (B-14).

## 22/11/2026: ningún código postal en la web (petición de Juan)
- Antes, 144 distritos sin nombre oficial ni barrios se llamaban "Distrito N · CP 21003 y 21001", y otros 500 llevaban "CP ..." en la segunda línea de la tabla (128 fichas). Ahora ningún código postal aparece en la web.
- Distritos sin barrios: si más de la mitad del distrito está fuera del núcleo principal, se nombran por sus núcleos de población del INE ("Distrito 8 · Gevora, Valdebotoa y otros núcleos"); si no, por sus dos calles principales del callejero del INE ("Distrito 1 · zona de Plaza Zocodover y calle Armas"). No se inventa ningún nombre.
- `preparar_zonas.py` guarda además `fuera_principal` (parte del distrito fuera del núcleo principal). `preparar_json.py`: función `etiqueta_zona()`. `generar_web.py`: la segunda línea ya no lleva CP y la nota de la tabla explica el nuevo criterio. `rankings_temas.py`: notas de metodología sin "códigos postales".
- `tests/test_distritos.py`: nueva comprobación "Ningún código postal en la web" (JSON y todo el HTML). `ejecutar_tests.py`: 21 OK, 0 FALLA.

## 22/11/2026: herramienta "¿Dónde puedo vivir con mi sueldo?" (Fase 2, funcionalidad 1)
- Nuevo `herramienta_sueldo.py`: página /donde-vivir-con-mi-sueldo/. Escribes tus ingresos netos al mes, el máximo para el alquiler (25, 30, 35 o 40 %) y la comunidad, y sale en qué ciudades entra el alquiler mediano de un piso y, dentro de cada una, en qué distritos y barrios (con enlace a su fila de la ficha). Incluye las ciudades donde la media no entra pero algún distrito sí. El resultado se puede compartir: la dirección guarda los datos (?sueldo=1800&pct=35).
- Solo datos que ya estaban en ciudades_nivel1.json; distritos con la misma regla que la ficha (menos de 30 inmuebles no se usan; 30-99 con *). Los nombres de distrito nunca llevan código postal (si el JSON lo trajera, se cambia por núcleos o calles). El cálculo se hace en el navegador: nada se envía ni se guarda.
- Parte fija para Google y para quien no tenga JavaScript: texto "Qué dicen los datos" calculado con los datos, tabla "Hasta dónde llega cada sueldo" (1.000 a 3.000 €), metodología y aviso de zonas turísticas.
- `generar_web.py`: solo 3 líneas (import, tarjeta en la portada y llamada en main() que añade la URL al sitemap).
- Nuevo `tests/test_sueldo.py` (8 comprobaciones). `ejecutar_tests.py`: 21 OK, 0 FALLA.
- Probado en Chromium (1280 px y 390 px): cálculo, filtro por comunidad, "ver más", desplegable de distritos, enlace con parámetros, sin scroll horizontal y sin errores de JavaScript. Firefox, Safari y móvil real sin probar (B-14).

## 21/11/2026: barrios de OpenStreetMap en todas las ciudades posibles (B-32)
- Con los archivos que faltaban (las consultas grandes se partieron en trozos de 5 ciudades), `zonas_osm.py` pone barrios en 654 distritos de 115 ciudades. Sin barrios por falta de datos en OSM: Huelva, Torrejón de Ardoz, Roquetas de Mar, San Fernando, Chiclana, Coslada, Alcalá de Guadaíra, Ávila y Calvià (y distritos sueltos de otras).
- Nombres de OSM que empiezan en minúscula se ponen con mayúscula inicial ("carme" → "Carme"), salvo artículos ("els Poetes").
- La meta description de los rankings de barrios usa el primer barrio del distrito (el nombre completo pasaba de 160 caracteres). Tests: 20 OK.

## 21/11/2026: datos estructurados de Dataset corregidos (aviso de Search Console)
- Search Console avisó: falta "description" (crítico), tipo de "creator" no válido y falta "license". Venían de las dos fuentes citadas en `isBasedOn` (SERPAVI y ADRH), no del Dataset principal.
- `FUENTES_LD` en `generar_web.py`: cada fuente lleva descripción, `creator` de tipo Organization con nombre y web, URL y licencia (INE: CC BY 4.0; Ministerio: su aviso legal, ver FUENTES.md).
- Nuevo test en `tests/test_seo.py`: todos los Dataset, también los anidados, con description de 50-5000 caracteres, creator Person/Organization con name y url, y license. Tests: todo OK.
- Tras publicar: en Search Console, "Validar corrección".

## 20/11/2026: barrios de OpenStreetMap y buscador de barrios (B-32)
- Juan aprueba OpenStreetMap para las ciudades sin datos municipales, con la cita en el pie. Nuevo `zonas_osm.py` (cruce de calles de OSM con el callejero del INE) y `osm_descarga.py` (página para bajar los datos desde el navegador de Juan).
- Primera tanda: 47 ciudades con barrios en algún distrito (Madrid, Barcelona, València, Murcia, Palma, Alicante, Córdoba, Vigo, Gijón, Granada…). Quedan las de los archivos que Overpass no devolvió.
- Comprobado con Sevilla y Málaga: OSM da casi los mismos barrios que los datos oficiales.
- Los distritos con nombre oficial (Madrid, Barcelona, València…) también muestran sus barrios debajo del nombre.
- Buscador de la portada: ahora encuentra barrios y distritos con nombre ("Triana" → Sevilla, distrito 6) y enlaza a su fila de la tabla (`#dN`).
- Pie: cita de OpenStreetMap y licencia ODbL. Tests: 20 OK.

## 20/11/2026: barrios con nombre en Las Palmas de Gran Canaria (B-32)
- `zonas_ciudades.py` añade Las Palmas: cada sección censal del Ayuntamiento se sitúa en su distrito del INE comparando sus calles con el callejero electoral del INE; hasta 5 barrios por distrito con al menos el 5 % de la población. Detalle fila a fila en `datos_municipales/35016_laspalmas_barrio_por_seccion_censal.csv`.
- Corrección menor: "Casablanca I" (la I final es un número romano). Tests: 20 OK.

## 20/11/2026: fondo siempre claro y enlaces sin subrayado
- Juan lo vio en el móvil con modo oscuro y la web salía con fondo azul oscuro. Se quita el modo oscuro: fondo blanco siempre (`color-scheme: light only`).
- Enlaces sin subrayado: en tablas y listas, nombre en negrita oscura con una flecha azul "›" (así se distinguen las filas con página propia); subrayado solo al pasar el ratón. Tests: 20 OK.

## 20/11/2026: diseño más sencillo y coherente entre páginas
- Petición de Juan: que la web se lea mejor y no líe al pasar de una página a otra. Solo cambian la plantilla y el CSS de `generar_web.py`; el contenido, las URL, los títulos y los datos estructurados son los mismos.
- Menú principal igual en todas las páginas (Ciudades, Rankings, Comunidades). Los enlaces dentro de la página (Resumen, Claves, Distritos…) van en una barra aparte, "En esta página", solo si hay 3 o más.
- Fondo blanco, un solo color de acento (azul oscuro), letra algo mayor, líneas de texto más cortas y el mismo ancho en todas las páginas. Miga de pan visible también en los 4 rankings generales.
- Pie nuevo de ancho completo, azul oscuro y letra pequeña: secciones, aviso legal, privacidad y cookies, fuentes con su fecha y licencia.
- Sigue sin fuentes ni recursos externos. Visto en Chromium (1280 px y 390 px): sin scroll horizontal. Tests: 20 OK, 0 FALLA.


## 20/11/2026: barrios con nombre en Málaga (B-32, B-22)
- Juan acepta la licencia CC BY-SA 4.0 de los datos de Málaga. `INCLUIR_MALAGA = True`; la nota bajo la tabla dice que esa lista de barrios va con CC BY-SA 4.0.

## 20/11/2026: barrios con nombre en Sevilla y Zaragoza (B-32)
- Nuevo `zonas_ciudades.py`: escribe en `zonas_nombradas.csv` los barrios de Sevilla (nombre del distrito municipal y sus barrios, ide.SEVILLA, CC BY 4.0) y las juntas de Zaragoza (cruce de secciones censales y juntas del Ayuntamiento). Málaga calculada pero sin publicar (licencia CC BY / CC BY-SA por aclarar).
- `zonas_nombradas.csv` tiene una columna opcional `nota` que la ficha muestra bajo la tabla para explicar cómo se asignaron los barrios (si falta, sale el texto de Valladolid). Tocado en `preparar_json.py`, `generar_web.py` y `zonas_valladolid.py` (solo para conservar la columna).
- Tests: 20 OK, 0 FALLA, 0 PENDIENTE.

## 20/11/2026: Rankings temáticos para búsquedas concretas (B-29)
- Nuevo `rankings_temas.py` con 5 páginas en /rankings/, cada una con tabla ordenable, texto "Qué dicen los datos" calculado solo con el JSON, enlaces a las fichas de ciudad, metodología, aviso de zonas turísticas y entrada en el sitemap:
  - `donde-mas-sube-el-alquiler/`: cambio del alquiler mediano 2019-2024 y 2023-2024, comparado con la renta del hogar (144 ciudades; 7 sin dato fiable en 2019).
  - `sueldo-para-vivir-de-alquiler/`: ingresos netos al mes para que el alquiler mediano no pase del 30 % (cálculo propio con una regla orientativa, explicado en la página).
  - `barrios-con-mas-renta/`: renta por hogar de los 843 distritos.
  - `barrios-con-el-alquiler-mas-caro/`: alquiler de los 812 distritos con 30 inmuebles o más (los de 30-99 con *).
  - `ciudades-mas-jovenes/`: edad media, menores de 18 y mayores de 65 (INE, ADRH).
- `generar_web.py` solo añade las 5 tarjetas a la portada y las URL al sitemap. Las piezas comunes (pie, cabecera, JSON-LD) se reutilizan, así que los cambios del pie llegan también a estas páginas.
- Nuevo `tests/test_rankings_temas.py` (7 comprobaciones: páginas en sitemap y portada, texto propio sin párrafos repetidos, enlaces a fichas, número de filas, valores de referencia y cálculos, distritos con menos de 30 inmuebles sin alquiler, metodología y año). `ejecutar_tests.py`: 20 OK, 0 FALLA.
- Visto en Chromium (1280 px y 390 px): sin scroll horizontal de página, tablas ordenables, sin errores de JavaScript.

## 20/11/2026: Páginas legales (B-04, en parte)
- Nuevo `paginas_legales.py`: aviso legal (LSSI art. 10), política de privacidad (RGPD) y política de cookies, en /aviso-legal/, /privacidad/ y /cookies/, enlazadas desde el pie de todas las páginas y en el sitemap. `generar_web.py` solo añade el enlace del pie y la llamada que escribe las páginas.
- La web no usa cookies, almacenamiento local ni recursos de otros sitios, así que no necesita aviso de cookies. Cuando haya publicidad habrá que añadir un aviso de consentimiento y actualizar privacidad y cookies ANTES de activarla.
- Mientras falten los datos del titular (TITULAR en `paginas_legales.py`), las páginas no se generan y el pie no las enlaza.
- Nuevo `tests/test_legales.py`: datos del titular en las páginas (con datos ficticios), enlaces del pie, sitemap y que la web siga sin cookies ni recursos externos. Probado en una copia con datos ficticios: 19 OK, 0 FALLA.
- No es asesoramiento legal.

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

## 22/11/2026: aviso legal más discreto
- Páginas legales con letra más pequeña (texto 15 px, títulos 18 px, cabecera reducida), solo en esas páginas (clases `legal-hero` y `legal-texto` en la constante CSS de `generar_web.py`).
- Datos del titular (nombre y correo) en una sola línea de letra pequeña y gris, sin negritas, al final del aviso legal (apartado 8) y de la política de privacidad (apartado 6). Los correos de las páginas legales ya no salen en azul y negrita, pero siguen siendo enlaces.
- Siguen publicados y accesibles desde el pie de todas las páginas (LSSI art. 10). `ACTUALIZADO` = 22/11/2026. Tests: 21 OK, 0 FALLA. No es asesoramiento legal.

## 23/11/2026: títulos sin el año
- Decisión de Juan: el `<title>` (lo que enseña Google) y `og:title` ya no llevan "(2024)", porque el año hace que el dato parezca viejo y puede quitar clics. Se quita en un solo sitio, `head()` de `generar_web.py`, así que vale para todas las páginas (fichas, rankings, comunidades, portada, sueldo y comparador). El resto del título no cambia.
- El año sigue en el H1 de los rankings, en el texto, en el pie y en los datos estructurados (JSON-LD), para que quede claro de qué año son los datos.
- Comprobado: solo cambian los 177 títulos y la fecha de generación; ningún otro byte de la web. Tests: `test_seo.py` exige que ningún título lleve año; `test_rankings_temas.py` y `test_sueldo.py` cambiados en consecuencia. 22 OK, 0 FALLA.
- Medir en Search Console (CTR de las fichas) 3-4 semanas después de publicarlo.

## 23/11/2026: revisión mensual de datos nuevos
- Nuevo `REVISION_DATOS.md`: qué fuentes se revisan, dónde mirar y el historial de revisiones. Tarea programada el día 1 de cada mes. Primera revisión: ninguna fuente tiene datos más recientes que los de la web. No se ha cambiado ningún dato ni la web.

# Informe de la Fase 0: auditoría de ciudadesendatos
18/11/2026

## 1. Qué he hecho
- La carpeta coincide con INSTRUCCIONES_PROYECTO.md: 151 ciudades, 130 con distritos (843), 156 páginas, mapa solo en Madrid y 40 nombres de distrito (Madrid y Valencia).
- Repositorio git creado con un commit de seguridad antes de tocar nada.
- Pipeline ejecutado entero, en menos de 2 minutos. **Los valores de referencia son correctos**: Madrid 868,75 / 53.213 / 19,6 %, Valencia 680,83 / 42.374 / 19,3 % y Valladolid 530,83 / 39.685 / 16,1 %. Al ejecutarlo de nuevo, la salida es idéntica a la anterior.
- Creado `tests/ejecutar_tests.py` (sin instalar nada: `python tests/ejecutar_tests.py`). Resultado: **10 OK, 0 fallos y 2 pendientes conocidos** (la fecha de actualización y los títulos largos).
- Probados el buscador, la ordenación de tablas y el mapa en un navegador Chromium, en tamaño escritorio y móvil: **20 de 20 OK**, sin errores de JavaScript. No lo he probado en Firefox, Safari ni en un móvil físico.
- Creados PROYECTO.md, BACKLOG.md, FUENTES.md y CHANGELOG.md.

## 2. Los 5 riesgos o mejoras más importantes

**1. La web no está publicada, así que hoy tiene cero visitas.** `BASE_URL` está vacío, por lo que no se genera sitemap ni canonical. No hay aviso legal, política de privacidad, analítica ni Search Console. Es lo que más impacto tiene y lo único que bloquea medir cualquier otra cosa. → Fase 1 (B-03, B-04, B-06).

**2. Falta la fecha de actualización que piden las licencias, y una licencia no está documentada.**
- El Aviso legal del INE (leído hoy) exige mencionar la fecha de actualización cuando figura en el original, y las condiciones del Ministerio también la piden. El pie dice "datos de 2024", pero no la fecha de actualización (B-01). Arreglarlo es fácil.
- La licencia del fichero SERPAVI no tiene un enlace oficial registrado. El PDF del SERPAVI que hay en la carpeta dice "Todos los derechos reservados" (sobre la publicación). Probablemente la base de datos tenga otras condiciones, pero hay que tener el enlace antes de publicar (B-02).
- El INE es **CC BY 4.0** según su Aviso legal. El pie de ine.es dice "BY-SA", pero enlaza a CC BY. fuentes.txt estaba desactualizado.

**3. Riesgo de "contenido delgado" ante Google.** Las 151 páginas siguen la misma plantilla. 110 de las 130 ciudades con distritos muestran "Distrito 3", "Distrito 7"…, que no le dicen nada a quien busca su barrio, y 21 ciudades no tienen ningún desglose interno. Hay 37 títulos de más de 70 caracteres (B-05). Lo que más diferencia las páginas es tener nombres reales de distrito (B-12) y datos nuevos por ciudad (Fase 3). Hasta entonces, conviene no multiplicar páginas (por ejemplo, no crear todavía páginas por distrito).

**4. Lectura engañosa en zonas turísticas.** Los 8 primeros del ranking "dónde más pesa el alquiler" son municipios de Málaga, casi todos de costa (Marbella, Fuengirola, Benalmádena…). Puede ser real, pero se mezcla la renta de los residentes con una demanda que viene de fuera. Ese ranking es justo el que más se compartiría, así que conviene un aviso visible en él, no solo al pie (B-13). Relacionado: el SERPAVI usa el seccionado del Censo 2021 y la renta es de 2024. Los códigos de distrito casan en 864 de 865, pero conviene contrastar 2 o 3 en el visor del INE (B-11).

**5. Mantenimiento: el pipeline no está preparado para el año que viene.** El año 2024 está escrito a mano en varios scripts (columnas `_24`, rangos de años), no existe `actualizar.py` y conviven scripts y CSV de la versión de 3 ciudades que ya no se usan (B-07, B-08, B-09, B-10). Cuando salgan los datos de 2025 habría que tocar cada script.

## 3. Las 10 funcionalidades candidatas mejor puntuadas

Puntuación de 1 a 5: **D** = demanda, **L** = datos con licencia, **Df** = diferencial, **M** = bajo mantenimiento, **R** = bajo riesgo.
**Aviso:** la columna D es una **hipótesis**. No tengo volúmenes de búsqueda medidos. Se valida con Search Console tras publicar y, antes, con el autocompletado de Google y Google Trends (puedo prepararte una lista de búsquedas para comprobar a mano).

| # | Funcionalidad | D | L | Df | M | R | Total | Datos y licencia (comprobado) |
|---|---|---|---|---|---|---|---|---|
| 1 | **"¿Dónde puedo vivir con mi sueldo?"** (ingresos → ciudades y distritos donde el alquiler no supera un %) | 4 | 5 | 4 | 5 | 4 | **22** | Ya tenemos alquiler (SERPAVI) y renta (INE, CC BY 4.0). Riesgo: hay que dejar claro que es la mediana de contratos vigentes, no de anuncios |
| 2 | **Comparador de 2 a 4 ciudades** | 4 | 5 | 3 | 5 | 5 | **22** | Mismos datos que ya están publicados. Solo hace falta JavaScript |
| 3 | **"Dónde más ha subido el alquiler"** (ranking de evolución 2019-2024 y 2015-2024 frente a la renta) | 4 | 5 | 4 | 4 | 4 | **21** | Serie SERPAVI 2011-2024 (144 de 151 ciudades completas) y renta INE 2015-2024, ya en el JSON. Es la historia de datos más citable |
| 4 | **Metaetiquetas e imágenes para compartir** (og:image por ciudad) | 3 | 5 | 3 | 5 | 5 | **21** | Sin datos nuevos. Multiplica el efecto de compartir. *Otro hilo ya trabaja en esto* |
| 5 | **Rankings por provincia y comunidad** | 3 | 5 | 3 | 5 | 4 | **20** | Datos existentes. Riesgo de páginas flojas si una provincia tiene 1 o 2 ciudades: crear solo las que tengan 3 o más |
| 6 | **Viviendas turísticas por municipio** | 4 | 4 | 4 | 4 | 4 | **20** | INE, estadística experimental semestral con mapas municipales, bajo el Aviso legal del INE (CC BY 4.0). Además ayuda a explicar el riesgo 4. Falta ver el formato de descarga y el último periodo |
| 7 | **Descarga de datos (CSV/JSON) y widget embebible** | 2 | 5 | 3 | 5 | 4 | **19** | CC BY 4.0 permite redistribuir citando. Atrae enlaces de estudiantes y medios más que búsquedas |
| 8 | **Precio y número de compraventas** (y después la calculadora alquilar o comprar) | 5 | 3 | 3 | 4 | 4 | **19** | Ministerio de Vivienda, "Transacciones inmobiliarias de vivienda": **CC BY 4.0**, trimestral, CSV. **Sin confirmar** que llegue a nivel municipal (hay que abrir el CSV). El "valor tasado por municipios" no tiene licencia visible en su ficha |
| 9 | **Paro registrado por municipio** | 3 | 5 | 2 | 4 | 5 | **19** | SEPE en datos.gob.es: **CC BY 4.0**, municipal, por sexo, edad y sector. Ojo: es paro registrado, no tasa de paro (no hay denominador oficial municipal) |
| 10 | **Mapa nacional y mapas reales de distritos** | 3 | 3 | 4 | 4 | 4 | **18** | Cartografía INE de secciones censales en SHAPE (2001-2026) y WFS. **La licencia de la cartografía no está explícita**: el Aviso legal habla de "información estadística". Hay que confirmarlo antes |

Quedan fuera del top 10 por ahora: la "ciudad ideal" con pesos (más compleja y de demanda incierta), la versión en inglés (mejor tras medir), clima, aire, criminalidad y educación (licencias y nivel municipal sin comprobar todavía) y las notas de corte (aplazadas).

## 4. Propuesta de orden
Mantengo tu orden, con un matiz: **la Fase 1 debe incluir B-01 y B-02** (fecha y licencia SERPAVI). Son condiciones de las licencias y no conviene publicar sin ellas. Después, en la Fase 2, propongo empezar por **1 + 2 + 3** (sueldo, comparador, evolución): usan solo datos que ya tenemos y son las más compartibles. El mapa nacional (que tú ponías en la Fase 2) lo bajaría hasta confirmar la licencia de la cartografía.

## 5. Qué necesito de ti
1. **Aprobar (o cambiar) la Fase 1.** Mi propuesta: B-01, B-02, B-04, B-07 y la publicación en GitHub Pages con las instrucciones paso a paso para tus cuentas.
2. **Decidir el dominio.** ¿Compras uno (p. ej. ciudadesendatos.es, sin comprobar si está libre) o empezamos con la dirección gratuita de GitHub Pages? Es la única pregunta que bloquea la Fase 1.

No es asesoramiento legal. Las licencias están leídas en las fuentes, pero conviene que las revises tú también antes de monetizar.

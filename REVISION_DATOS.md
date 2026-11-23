# Revisión mensual de datos nuevos

Una tarea programada revisa el día 1 de cada mes, a las 8:47 (hora de Madrid), si las fuentes oficiales han publicado datos más recientes que los de la web. Solo informa: no descarga ni cambia datos sin la aprobación de Juan.

## Qué se comprueba
| Fuente (FUENTES.md) | Versión en la web | Dónde mirar | Cuándo suele salir la siguiente |
|---|---|---|---|
| 1. Alquiler, SERPAVI (Ministerio de Vivienda) | BD 2011-2024, fichero `2026-03_09_bd_SERPAVI_2011-2024 - DEFINITIVO WEB_v2.xlsx` (metadatos del 08/07/2026) | https://www.mivau.gob.es/vivienda/alquila-bien-es-tu-derecho/serpavi → enlace "BD Sistema Estatal Índices de Alquiler de Vivienda (Xlsx)": ver si el nombre del fichero cambia o pasa a 2011-2025 | Una vez al año; la de 2024 salió en marzo de 2026 |
| 2 y 3. Renta y demografía, ADRH (INE) | Año 2024, publicado el 19/10/2026 | https://www.ine.es/dyngs/INEbase/es/operacion.htm?c=Estadistica_C&cid=1254736177088&menu=ultiDatos&idp=1254735976608 → "Últimos datos" | Una vez al año, en otoño (el año 2025 se espera hacia octubre de 2027) |
| 5. Callejero del censo electoral (INE) | Julio de 2026 (`caj_esp_072026`) | https://www.ine.es/dyngs/DAB/es/index.htm?cid=1390 → el fichero de variaciones dice entre qué callejeros va | Enero y julio (el de enero de 2027 se espera a principios de 2027) |
| 4 y 6. Nombres de distrito y barrios municipales (Barcelona, Bilbao, Sevilla, Zaragoza, Málaga, Las Palmas, Valladolid) | Ver fechas en FUENTES.md | Portales de datos abiertos de cada ayuntamiento | Sin calendario; cambian poco. Basta mirarlos cada 3 meses |
| 7. OpenStreetMap | Consulta del 20/11/2026 | No hace falta revisarlo cada mes | Continuo |

Si hay algo nuevo, Juan descarga el fichero en `datos_originales/` (instrucciones clic a clic en el aviso), se cambia el año en `config.py` si toca y se ejecuta `python actualizar.py`. Los valores de referencia de `config.py` cambiarán con datos de otro año: hay que revisarlos y actualizarlos a propósito.

## Historial
| Fecha | SERPAVI | ADRH (INE) | Callejero (INE) | Municipales | Resultado |
|---|---|---|---|---|---|
| 23/11/2026 | Sin cambios (BD 2011-2024, mismo fichero) | Sin cambios (año 2024, 19/10/2026) | Sin cambios (julio 2026) | No revisadas | Nada que actualizar |

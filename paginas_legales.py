"""Páginas legales de ciudadesendatos: aviso legal, privacidad y cookies (B-04).

generar_web.py llama a paginas() y a enlaces_pie(); este módulo no toca nada más.

IMPORTANTE: no es asesoramiento legal. Los textos siguen la LSSI (Ley 34/2002) y el
RGPD para una web informativa sin formularios, sin cookies y sin analítica. Si se
añade analítica, publicidad o un formulario, hay que revisar privacidad y cookies
ANTES de publicarlo (y poner un aviso de consentimiento si se instalan cookies).

Datos del titular: la LSSI (art. 10) obliga a publicarlos. Mientras falte alguno,
las páginas no se generan y el pie no las enlaza (el test lo marca como PENDIENTE).
"""
import html

# ---------------------------------------------------------------- datos del titular
# Rellénalos exactamente como quieres que aparezcan en la web (serán públicos).
TITULAR = {
    "nombre": "",       # nombre y dos apellidos
    "nif": "",          # DNI con letra, p. ej. 12345678Z
    "domicilio": "",    # calle, número, código postal, ciudad (provincia)
    "email": "",        # correo de contacto de la web
}

ACTUALIZADO = "20/11/2026"   # cámbialo cada vez que cambie el texto de alguna página legal
DOMINIO = "ciudadesendatos.es"

PAGINAS = {   # carpeta -> título del enlace
    "aviso-legal": "Aviso legal",
    "privacidad": "Política de privacidad",
    "cookies": "Política de cookies",
}


def completo():
    return all(str(v).strip() for v in TITULAR.values())


def esc(s):
    return html.escape(str(s), quote=True)


def enlaces_pie(root):
    """Línea de enlaces legales para el pie. Vacía si faltan los datos del titular."""
    if not completo():
        return ""
    return ('<nav class="legal" aria-label="Información legal">'
            + " · ".join(f'<a href="{root}{c}/">{t}</a>' for c, t in PAGINAS.items()) + "</nav>")


def _titular_html():
    t = {k: esc(v.strip()) for k, v in TITULAR.items()}
    return (f'<ul><li><strong>Titular:</strong> {t["nombre"]}</li>'
            f'<li><strong>NIF:</strong> {t["nif"]}</li>'
            f'<li><strong>Domicilio:</strong> {t["domicilio"]}</li>'
            f'<li><strong>Correo electrónico:</strong> <a href="mailto:{t["email"]}">{t["email"]}</a></li>'
            f'<li><strong>Sitio web:</strong> {DOMINIO}</li></ul>')


def _email():
    e = esc(TITULAR["email"].strip())
    return f'<a href="mailto:{e}">{e}</a>'


def _aviso_legal(root):
    return f"""
<section><h2>1. Datos del titular</h2>
<p>En cumplimiento del artículo 10 de la Ley 34/2002, de 11 de julio, de servicios de la sociedad de la información y de comercio electrónico (LSSI), se informa de que el titular de este sitio web es:</p>
{_titular_html()}</section>
<section><h2>2. Objeto</h2>
<p>{DOMINIO} es un portal informativo y gratuito que reúne datos oficiales sobre las ciudades de España (alquiler, renta de los hogares, población y otros) y los presenta en fichas, rankings y tablas. El sitio puede mostrar publicidad o enlaces de afiliación, que se identificarán como tales.</p></section>
<section><h2>3. Condiciones de uso</h2>
<p>El acceso a la web es libre y no requiere registro. Al usarla te comprometes a hacerlo de forma lícita y a no dañar su funcionamiento. El titular puede modificar los contenidos y estas condiciones en cualquier momento; la versión vigente es la publicada en esta página.</p></section>
<section><h2>4. Origen y fiabilidad de los datos</h2>
<p>Los datos proceden de fuentes oficiales (Ministerio de Vivienda y Agenda Urbana, Instituto Nacional de Estadística y, en algunos casos, ayuntamientos), que se citan en cada página junto con su fecha de actualización. Algunos indicadores, como el peso del alquiler sobre la renta, son estimaciones propias y se presentan como tales; la <a href="{root}#ciudades">ficha de cada ciudad</a> explica cómo se calculan.</p>
<p>Se procura que la información sea exacta y esté al día, pero puede contener errores o no reflejar cambios posteriores de las fuentes. Tiene carácter <strong>solo informativo</strong> y no constituye asesoramiento inmobiliario, financiero, fiscal ni de ningún otro tipo. Esta web no está vinculada ni patrocinada por el INE, el Ministerio de Vivienda ni ningún ayuntamiento.</p></section>
<section><h2>5. Propiedad intelectual y reutilización</h2>
<p>Los datos elaborados y los textos propios de {DOMINIO} se publican con licencia <a href="https://creativecommons.org/licenses/by/4.0/deed.es" rel="license">Creative Commons Atribución 4.0 (CC BY 4.0)</a>: puedes copiarlos, adaptarlos y usarlos, también con fines comerciales, citando {DOMINIO} con un enlace a la página de origen. Los datos de origen mantienen la licencia de sus fuentes, indicada en cada página.</p></section>
<section><h2>6. Enlaces a otros sitios</h2>
<p>La web enlaza a páginas de terceros (por ejemplo, las fuentes oficiales). El titular no controla su contenido y no responde de él. Si detectas un enlace a un contenido ilícito, escríbenos y lo retiraremos.</p></section>
<section><h2>7. Responsabilidad</h2>
<p>En la medida en que lo permita la ley, el titular no responde de los daños que puedan derivarse del uso de la información de esta web ni de interrupciones del servicio.</p></section>
<section><h2>8. Contacto y legislación aplicable</h2>
<p>Para cualquier consulta, error en los datos o aviso, escribe a {_email()}. Estas condiciones se rigen por la legislación española.</p></section>"""


def _privacidad(root):
    return f"""
<section><h2>1. Responsable del tratamiento</h2>
{_titular_html()}</section>
<section><h2>2. Qué datos recogemos</h2>
<p>Esta web <strong>no tiene formularios, registro ni comentarios</strong>, y no usa cookies ni herramientas de analítica o publicidad. El titular no recoge datos personales de quienes la visitan.</p></section>
<section><h2>3. Alojamiento de la web</h2>
<p>La web se aloja en GitHub Pages, un servicio de GitHub, Inc. (Estados Unidos). Como ocurre con cualquier página, al visitarla tu navegador envía al servidor datos técnicos como la dirección IP, el tipo de navegador y la página solicitada. GitHub puede registrarlos para servir la web y por seguridad, según su <a href="https://docs.github.com/es/site-policy/privacy-policies/github-general-privacy-statement">declaración de privacidad</a>. El titular no tiene acceso a esos registros.</p>
<p>La base jurídica es el interés legítimo en ofrecer la web de forma segura (artículo 6.1.f del RGPD). Los datos pueden tratarse en Estados Unidos; GitHub declara cumplir el Marco de Privacidad de Datos UE-EE. UU., que cuenta con una decisión de adecuación de la Comisión Europea.</p></section>
<section><h2>4. Si nos escribes por correo electrónico</h2>
<p>Si escribes a {_email()}, usaremos tu dirección de correo, tu nombre si lo indicas y el contenido del mensaje solo para responderte. La base jurídica es tu consentimiento al escribirnos (artículo 6.1.a del RGPD). Conservaremos el mensaje mientras sea necesario para atender tu consulta y lo borraremos después, salvo que una ley obligue a guardarlo. No cedemos estos datos a nadie, salvo obligación legal; el proveedor del servicio de correo los trata por cuenta del titular.</p></section>
<section><h2>5. Tus derechos</h2>
<p>Puedes pedir el acceso, la rectificación o la supresión de tus datos, oponerte a su tratamiento, pedir su limitación o su portabilidad y retirar tu consentimiento en cualquier momento, escribiendo a {_email()}. Si consideras que no se han respetado tus derechos, puedes presentar una reclamación ante la Agencia Española de Protección de Datos (<a href="https://www.aepd.es">www.aepd.es</a>).</p>
<p>No se toman decisiones automatizadas ni se elaboran perfiles con tus datos.</p></section>
<section><h2>6. Cambios en esta política</h2>
<p>Si en el futuro la web incorpora analítica, publicidad o algún formulario, esta política se actualizará <strong>antes</strong> de activarlos y, cuando la ley lo exija, se pedirá tu consentimiento. Consulta también la <a href="{root}cookies/">política de cookies</a>.</p></section>"""


def _cookies(root):
    return f"""
<section><h2>1. Qué son las cookies</h2>
<p>Las cookies son pequeños archivos que algunas webs guardan en tu navegador para recordar información sobre tu visita. Otras tecnologías parecidas, como el almacenamiento local del navegador, funcionan de forma similar.</p></section>
<section><h2>2. Cookies que usa esta web</h2>
<p><strong>Ninguna.</strong> Esta web no instala cookies propias ni de terceros, ni usa el almacenamiento local del navegador, y no carga contenidos de otros sitios (fuentes, vídeos, analítica o publicidad). Por eso no ves ningún aviso de cookies: la ley (artículo 22.2 de la LSSI) solo obliga a pedir consentimiento cuando se instalan cookies que no son técnicas.</p></section>
<section><h2>3. Si en el futuro se añade publicidad</h2>
<p>Si la web llega a mostrar publicidad (por ejemplo, de Google AdSense) o a usar analítica con cookies, estas no se instalarán sin tu consentimiento: verás un aviso que te permitirá aceptarlas, rechazarlas o elegir cuáles, con la misma facilidad, y esta página se actualizará con la lista de cookies, quién las instala, para qué y durante cuánto tiempo.</p></section>
<section><h2>4. Cómo gestionar las cookies en tu navegador</h2>
<p>Puedes ver y borrar las cookies, o bloquearlas, en la configuración de tu navegador (normalmente en el apartado de privacidad o seguridad). Consulta la ayuda de tu navegador para ver cómo hacerlo.</p>
<p>Más información sobre cómo tratamos los datos en la <a href="{root}privacidad/">política de privacidad</a>.</p></section>"""


CONTENIDO = {
    "aviso-legal": (_aviso_legal, "Aviso legal de ciudadesendatos",
                    "Titular, condiciones de uso, origen de los datos, licencia y responsabilidad del portal ciudadesendatos."),
    "privacidad": (_privacidad, "Política de privacidad de ciudadesendatos",
                   "Qué datos personales trata ciudadesendatos (ninguno de sus visitantes), alojamiento en GitHub Pages y tus derechos."),
    "cookies": (_cookies, "Política de cookies de ciudadesendatos",
                "ciudadesendatos no usa cookies ni almacenamiento local. Qué pasaría si se añadiera publicidad y cómo gestionar las cookies."),
}


def paginas(head, cabecera, pie, fin, sitio_url):
    """Devuelve {carpeta: html}. Vacío si faltan los datos del titular.

    Recibe las piezas comunes de generar_web.py para no duplicar la plantilla.
    """
    if not completo():
        return {}
    root = "../"
    salida = {}
    for carpeta, (cuerpo, titulo, desc) in CONTENIDO.items():
        ruta = f"{carpeta}/"
        ld = [{"@context": "https://schema.org", "@type": "WebPage", "name": titulo, "description": desc,
               "inLanguage": "es", **({"url": f"{sitio_url}/{ruta}"} if sitio_url else {})}]
        h1 = PAGINAS[carpeta]
        salida[carpeta] = (head(titulo, desc, root, ruta, ld) + cabecera(root, [])
                           + f'<div class="hero"><div><h1>{h1}</h1>'
                           + f'<p class="lead">Última actualización: {ACTUALIZADO}.</p></div></div>'
                           + f'<main class="legal-texto">{cuerpo(root)}{pie(root)}</main>' + fin(root))
    return salida

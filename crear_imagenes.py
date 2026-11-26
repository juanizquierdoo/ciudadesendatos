"""Crea las imágenes fijas de la web en recursos/: logo, favicons e imagen para compartir.

Solo hace falta ejecutarlo si se quiere cambiar el diseño; las imágenes ya están guardadas en recursos/.
Necesita Pillow:  pip install pillow

Logo (26/11/2026): chincheta de mapa blanca con tres barras dentro, sobre un cuadrado verde
redondeado ("ciudad" + "datos"). La geometría está en unidades de un lienzo de 512 x 512 y se
usa igual para el SVG y para los PNG, así que siempre coinciden.

Archivos que crea:
- favicon.svg            icono vectorial (navegadores modernos y Google)
- favicon.ico            16, 32 y 48 px (navegadores antiguos y /favicon.ico)
- favicon.png            48 x 48
- icono-192.png          192 x 192 (Google prefiere múltiplos de 48 px; Android)
- apple-touch-icon.png   180 x 180, sin esquinas transparentes (iPhone/iPad las redondea solo)
- logo-512.png           512 x 512, logo de la organización en los datos estructurados
- og.png                 1200 x 630, imagen para compartir en redes
"""
import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

base = Path(__file__).parent
REC = base / "recursos"
REC.mkdir(exist_ok=True)
FONDO, TINTA, ACENTO, VERDE = "#1f2933", "#ffffff", "#5fe0b0", "#0f7a5b"

# ---- geometría del logo (lienzo 512 x 512)
RADIO_FONDO = 112
PIN_C, PIN_R, PIN_PUNTA = (256, 196), 186, (256, 470)
BARRAS = [(160, 178, 214, 288), (229, 112, 283, 288), (298, 148, 352, 288)]   # x0, y0, x1, y1
RADIO_BARRA = 10


def _tangentes():
    """Puntos donde los lados de la chincheta tocan el círculo."""
    cx, cy = PIN_C
    d = PIN_PUNTA[1] - cy
    t = math.acos(PIN_R / d)
    dx, dy = PIN_R * math.sin(t), PIN_R * math.cos(t)
    return (cx - dx, cy + dy), (cx + dx, cy + dy)


def logo_svg():
    (x1, y1), (x2, y2) = _tangentes()
    cx, cy = PIN_C
    barras = "".join(f'<rect x="{a}" y="{b}" width="{c - a}" height="{d - b}" rx="{RADIO_BARRA}"/>' for a, b, c, d in BARRAS)
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512">'
            f'<rect width="512" height="512" rx="{RADIO_FONDO}" fill="{VERDE}"/>'
            f'<path d="M{PIN_PUNTA[0]} {PIN_PUNTA[1]} L{x1:.1f} {y1:.1f} A{PIN_R} {PIN_R} 0 1 1 {x2:.1f} {y2:.1f} Z" fill="{TINTA}"/>'
            f'<g fill="{VERDE}">{barras}</g></svg>\n')


def logo(tam, esquinas=True):
    """Logo en PNG de tam x tam. Se dibuja 4 veces más grande y se reduce para que los bordes queden suaves."""
    S = 2048
    k = S / 512
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    if esquinas:
        d.rounded_rectangle([0, 0, S - 1, S - 1], radius=RADIO_FONDO * k, fill=VERDE)
    else:
        d.rectangle([0, 0, S, S], fill=VERDE)
    cx, cy = PIN_C
    d.ellipse([(cx - PIN_R) * k, (cy - PIN_R) * k, (cx + PIN_R) * k, (cy + PIN_R) * k], fill=TINTA)
    (x1, y1), (x2, y2) = _tangentes()
    d.polygon([(x1 * k, y1 * k), (PIN_PUNTA[0] * k, PIN_PUNTA[1] * k), (x2 * k, y2 * k), (cx * k, cy * k)], fill=TINTA)
    for a, b, c, e in BARRAS:
        d.rounded_rectangle([a * k, b * k, c * k, e * k], radius=RADIO_BARRA * k, fill=VERDE)
    return im.resize((tam, tam), Image.LANCZOS)


def fuente(tam, negrita=True):
    candidatas = (["arialbd.ttf", "Lato-Bold.ttf", "DejaVuSans-Bold.ttf"] if negrita
                  else ["arial.ttf", "Lato-Regular.ttf", "DejaVuSans.ttf"])
    for f in candidatas:
        try:
            return ImageFont.truetype(f, tam)
        except OSError:
            for d in ("/usr/share/fonts/truetype/lato", "/usr/share/fonts/truetype/dejavu"):
                try:
                    return ImageFont.truetype(f"{d}/{f}", tam)
                except OSError:
                    pass
    return ImageFont.load_default(size=tam)


if __name__ == "__main__":
    # imagen para compartir: 1200 x 630
    img = Image.new("RGB", (1200, 630), FONDO)
    dib = ImageDraw.Draw(img)
    marca = logo(140)
    img.paste(marca, (90, 100), marca)
    f1 = fuente(92)
    x = 90
    for trozo, col in (("ciudades", TINTA), ("en", ACENTO), ("datos", TINTA)):
        dib.text((x, 270), trozo, font=f1, fill=col)
        x += dib.textlength(trozo, font=f1)
    dib.text((90, 400), "Alquiler y renta en las ciudades de España", font=fuente(44, False), fill=TINTA)
    dib.text((90, 462), "Elaboración propia con datos oficiales", font=fuente(34, False), fill="#9ba7b0")
    dib.rectangle([0, 600, 1200, 630], fill=VERDE)
    img.save(REC / "og.png", optimize=True)

    # logo e iconos
    (REC / "favicon.svg").write_text(logo_svg(), encoding="utf-8")
    logo(48).save(REC / "favicon.png", optimize=True)
    logo(192).save(REC / "icono-192.png", optimize=True)
    logo(512).save(REC / "logo-512.png", optimize=True)
    logo(180, esquinas=False).convert("RGB").save(REC / "apple-touch-icon.png", optimize=True)
    logo(256).save(REC / "favicon.ico", sizes=[(16, 16), (32, 32), (48, 48)])
    print("Imágenes creadas en", REC)

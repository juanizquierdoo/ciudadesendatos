"""Crea las imágenes fijas de la web en recursos/: og.png (para compartir en redes) y favicon.png/.ico.

Solo hace falta ejecutarlo si se quiere cambiar el diseño; las imágenes ya están guardadas en recursos/.
Necesita Pillow:  pip install pillow
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

base = Path(__file__).parent
REC = base / "recursos"
REC.mkdir(exist_ok=True)
FONDO, TINTA, ACENTO, VERDE = "#1f2933", "#ffffff", "#5fe0b0", "#0f7a5b"


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


def barras(dib, x, y, ancho, alto, color):
    """Pequeño gráfico de barras, el símbolo de la web."""
    alturas = [0.45, 0.7, 0.55, 1.0]
    sep = ancho / (len(alturas) * 3 - 1)
    for i, h in enumerate(alturas):
        x0 = x + i * 3 * sep
        dib.rounded_rectangle([x0, y + alto * (1 - h), x0 + 2 * sep, y + alto], radius=sep * 0.4, fill=color)


# imagen para compartir: 1200 x 630
img = Image.new("RGB", (1200, 630), FONDO)
dib = ImageDraw.Draw(img)
barras(dib, 90, 120, 120, 110, ACENTO)
f1 = fuente(92)
x = 90
for trozo, col in (("ciudades", TINTA), ("en", ACENTO), ("datos", TINTA)):
    dib.text((x, 270), trozo, font=f1, fill=col)
    x += dib.textlength(trozo, font=f1)
dib.text((90, 400), "Alquiler y renta en las ciudades de España", font=fuente(44, False), fill=TINTA)
dib.text((90, 462), "Elaboración propia con datos oficiales", font=fuente(34, False), fill="#9ba7b0")
dib.rectangle([0, 600, 1200, 630], fill=VERDE)
img.save(REC / "og.png", optimize=True)

# favicon: 48 x 48 (y .ico con varios tamaños)
ico = Image.new("RGBA", (192, 192), (0, 0, 0, 0))
d2 = ImageDraw.Draw(ico)
d2.rounded_rectangle([0, 0, 191, 191], radius=36, fill=VERDE)
barras(d2, 34, 40, 124, 112, TINTA)
ico.resize((48, 48), Image.LANCZOS).save(REC / "favicon.png", optimize=True)
ico.save(REC / "favicon.ico", sizes=[(16, 16), (32, 32), (48, 48)])
print("Imágenes creadas en", REC)

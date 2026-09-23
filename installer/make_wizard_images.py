"""
Generates Inno Setup wizard BMPs for Chalchitra.
Run once: python installer/make_wizard_images.py
"""
import os
from PIL import Image, ImageDraw, ImageFont

BG_DARK      = (11, 10, 15)
BG_GRAD_TOP  = (26, 21, 48)
BG_GRAD_BOT  = (11, 10, 15)
PURPLE       = (167, 139, 250)
MINT         = (110, 231, 183)
WHITE        = (232, 226, 240)
TEXT_DIM     = (200, 191, 216)

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_LARGE = os.path.join(HERE, "wizard-large.bmp")
OUT_SMALL = os.path.join(HERE, "wizard-small.bmp")

def find_system_font():
    for name in ("segoeuib.ttf", "SegoeUI-Bold.ttf", "arialbd.ttf", "Arial Bold.ttf"):
        for path in (r"C:\Windows\Fonts", r"C:\Windows\System32\Fonts"):
            full = os.path.join(path, name)
            if os.path.exists(full):
                return full
    return None

def lerp(a, b, t):
    return int(a + (b - a) * t)

def make_gradient(width, height, c1, c2):
    img = Image.new("RGB", (width, height), c1)
    px = img.load()
    for y in range(height):
        t = y / max(1, height - 1)
        r, g, b = lerp(c1[0], c2[0], t), lerp(c1[1], c2[1], t), lerp(c1[2], c2[2], t)
        for x in range(width):
            px[x, y] = (r, g, b)
    return img

def draw_logo(draw, cx, cy, size):
    s = size
    pad = int(s * 0.08)
    x0, y0 = cx - s // 2, cy - s // 2
    x1, y1 = x0 + s, y0 + s
    radius = int(s * 0.22)
    draw.rounded_rectangle([x0, y0, x1, y1], radius=radius, fill=BG_DARK)
    draw.polygon([(x0 + int(s*0.28), y0 + int(s*0.33)), (x0 + int(s*0.28), y0 + int(s*0.67)), (x0 + int(s*0.53), y0 + int(s*0.50))], fill=PURPLE)
    draw.polygon([(x0 + int(s*0.44), y0 + int(s*0.27)), (x0 + int(s*0.44), y0 + int(s*0.73)), (x0 + int(s*0.75), y0 + int(s*0.50))], fill=MINT)

def build_large(path):
    W, H = 164, 314
    img = make_gradient(W, H, BG_GRAD_TOP, BG_GRAD_BOT)
    draw = ImageDraw.Draw(img)
    draw_logo(draw, W // 2, 110, 96)
    font_path = find_system_font()
    try:
        font_title = ImageFont.truetype(font_path, 18) if font_path else ImageFont.load_default()
        font_sub   = ImageFont.truetype(font_path, 10) if font_path else ImageFont.load_default()
    except Exception:
        font_title, font_sub = ImageFont.load_default(), ImageFont.load_default()
    draw.text(((W - draw.textbbox((0, 0), "Chalchitra", font=font_title)[2]) // 2, 200), "Chalchitra", fill=WHITE, font=font_title)
    draw.text(((W - draw.textbbox((0, 0), "by AirSilo", font=font_sub)[2]) // 2, 226), "by AirSilo", fill=TEXT_DIM, font=font_sub)
    draw.rectangle([60, 250, 104, 252], fill=MINT)
    img.save(path, "BMP")
    print(f"Wrote {path}")

def build_small(path):
    W, H = 55, 55
    img = Image.new("RGB", (W, H), BG_DARK)
    draw = ImageDraw.Draw(img)
    draw_logo(draw, W // 2, H // 2, 46)
    img.save(path, "BMP")
    print(f"Wrote {path}")

if __name__ == "__main__":
    build_large(OUT_LARGE)
    build_small(OUT_SMALL)
    print("Done. Wizard images ready.")
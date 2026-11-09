#!/usr/bin/env python3
"""Generates every picture used by the Enerlytix site (PNG + SVG).
Run:  python tools/make_images.py   (needs Pillow)"""
import math, random
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

OUT = Path(__file__).resolve().parent.parent / "assets" / "images"
OUT.mkdir(parents=True, exist_ok=True)
INK, DEEP, TEAL, AMBER, MIST, WHITE = "#08222F", "#0D3345", "#12B5A0", "#F5A623", "#E8F1EF", "#FFFFFF"
S = 2  # supersample factor


def font(size, bold=True):
    for p in ("/usr/share/fonts/opentype/inter/Inter-%s.otf" % ("Bold" if bold else "Regular"),
              "/usr/share/fonts/truetype/dejavu/DejaVuSans%s.ttf" % ("-Bold" if bold else "")):
        try:
            return ImageFont.truetype(p, size * S)
        except OSError:
            pass
    return ImageFont.load_default()


def canvas(w, h, top=INK, bottom=DEEP):
    im = Image.new("RGB", (w * S, h * S), top)
    px = ImageDraw.Draw(im)
    for y in range(h * S):
        t = y / (h * S)
        c = [int(int(top[i:i + 2], 16) * (1 - t) + int(bottom[i:i + 2], 16) * t) for i in (1, 3, 5)]
        px.line([(0, y), (w * S, y)], fill=tuple(c))
    return im, ImageDraw.Draw(im, "RGBA")


def save(im, name, w, h):
    im.resize((w, h), Image.LANCZOS).save(OUT / name, optimize=True)


def grid(d, w, h, step=80):
    for x in range(0, w, step):
        d.line([(x * S, 0), (x * S, h * S)], fill=(255, 255, 255, 14), width=S)
    for y in range(0, h, step):
        d.line([(0, y * S), (w * S, y * S)], fill=(255, 255, 255, 14), width=S)


def label(d, xy, text, size=26, fill=WHITE, bold=True):
    d.text((xy[0] * S, xy[1] * S), text, font=font(size, bold), fill=fill)


# 1 ── Forecast ─────────────────────────────────────────────────────────
def forecast():
    W, H = 1200, 800
    im, d = canvas(W, H); grid(d, W, H)
    pts = lambda f: [(x * S, (680 - f(x)) * S) for x in range(100, 1101, 5)]
    base = lambda x: 460 * math.exp(-((x - 600) / 230) ** 2)
    up = pts(lambda x: base(x) * 1.14 + 22); dn = pts(lambda x: base(x) * .86 - 4)
    d.polygon(up + dn[::-1], fill=(18, 181, 160, 70))
    d.line(pts(base), fill=TEAL, width=7 * S, joint="curve")
    rnd = random.Random(4)
    act = [(x * S, (680 - base(x) * (1 + rnd.uniform(-.07, .07)) - (18 if x > 560 else 0)) * S)
           for x in range(100, 1101, 18)]
    d.line(act, fill=AMBER, width=4 * S, joint="curve")
    for p in act[::3]:
        d.ellipse([p[0] - 7 * S, p[1] - 7 * S, p[0] + 7 * S, p[1] + 7 * S], fill=AMBER)
    d.line([(100 * S, 680 * S), (1100 * S, 680 * S)], fill=(255, 255, 255, 90), width=2 * S)
    label(d, (100, 70), "Renewable-energy forecasting", 44)
    label(d, (100, 130), "Predicted vs. observed generation (illustrative)", 26, MIST, False)
    save(im, "forecast.png", W, H)


# 2 ── Smart grid ───────────────────────────────────────────────────────
def smartgrid():
    W, H = 1200, 800
    im, d = canvas(W, H, DEEP, INK); grid(d, W, H)
    rnd = random.Random(11)
    hub = (600, 400)
    nodes = [(hub[0] + math.cos(a) * r, hub[1] + math.sin(a) * r * .72)
             for r, n in ((190, 6), (340, 10), (470, 14))
             for a in [2 * math.pi * i / n + r for i in range(n)]]
    for n in nodes:
        near = sorted(nodes + [hub], key=lambda m: (m[0] - n[0]) ** 2 + (m[1] - n[1]) ** 2)[1:3]
        for m in near:
            d.line([(n[0] * S, n[1] * S), (m[0] * S, m[1] * S)], fill=(18, 181, 160, 120), width=2 * S)
    for n in nodes:
        c = AMBER if rnd.random() < .22 else TEAL
        d.ellipse([(n[0] - 11) * S, (n[1] - 11) * S, (n[0] + 11) * S, (n[1] + 11) * S], fill=c)
    for r, a in ((46, 40), (30, 90)):
        d.ellipse([(hub[0] - r) * S, (hub[1] - r) * S, (hub[0] + r) * S, (hub[1] + r) * S],
                  fill=(245, 166, 35, a if r == 46 else 255))
    label(d, (60, 56), "Smart grids & distributed energy", 40)
    save(im, "smartgrid.png", W, H)


# 3 ── Battery intelligence ─────────────────────────────────────────────
def battery():
    W, H = 1200, 800
    im, d = canvas(W, H); grid(d, W, H)
    levels = [.95, .82, .7, .55, .9, .38, .76, .6]
    for i, lv in enumerate(levels):
        x, y, w, h = (130 + (i % 4) * 250) * S, (200 + (i // 4) * 260) * S, 190 * S, 200 * S
        d.rounded_rectangle([x, y, x + w, y + h], 22 * S, outline=(255, 255, 255, 150), width=4 * S)
        d.rounded_rectangle([x + 60 * S, y - 16 * S, x + 130 * S, y], 6 * S, fill=(255, 255, 255, 150))
        col = AMBER if lv < .5 else TEAL
        d.rounded_rectangle([x + 14 * S, y + h - 14 * S - (h - 28 * S) * lv, x + w - 14 * S, y + h - 14 * S],
                            12 * S, fill=col)
    label(d, (130, 70), "Battery intelligence & storage optimisation", 38)
    save(im, "battery.png", W, H)


# 4 ── AI network ───────────────────────────────────────────────────────
def ainet():
    W, H = 1200, 800
    im, d = canvas(W, H, DEEP, INK); grid(d, W, H)
    layers, rnd = [4, 6, 6, 3], random.Random(2)
    xs = [220, 470, 720, 970]
    pos = [[(xs[i], 400 + (j - (n - 1) / 2) * 95) for j in range(n)] for i, n in enumerate(layers)]
    for a, b in zip(pos, pos[1:]):
        for p in a:
            for q in b:
                d.line([(p[0] * S, p[1] * S), (q[0] * S, q[1] * S)],
                       fill=(255, 255, 255, 30 + rnd.randint(0, 45)), width=S)
    for i, layer in enumerate(pos):
        for p in layer:
            c = AMBER if i == 3 else TEAL
            d.ellipse([(p[0] - 20) * S, (p[1] - 20) * S, (p[0] + 20) * S, (p[1] + 20) * S], fill=c)
    label(d, (60, 56), "AI-powered energy intelligence", 40)
    save(im, "ai-network.png", W, H)


# 5 ── Social card, logo PNGs, favicon ─────────────────────────────────
def mark(d, x, y, s, fg=WHITE, accent=AMBER):
    """Logo mark: three bars forming an 'E' with a pulse dot."""
    u = s / 10
    for i, wdt in enumerate((8, 6, 8)):
        d.rounded_rectangle([x + 1 * u * S, (y + (1.4 + i * 3) * u) * S,
                             (x + (1 + wdt) * u) * S, (y + (2.9 + i * 3) * u) * S], u * .75 * S, fill=fg)
    d.ellipse([(x + 8.2 * u) * S, (y + 4.5 * u) * S, (x + 9.8 * u) * S, (y + 6.1 * u) * S], fill=accent)


def social():
    W, H = 1200, 630
    im, d = canvas(W, H); grid(d, W, H, 60)
    for k, c in enumerate((TEAL, AMBER)):
        pts = [(x * S, (520 - 210 * math.exp(-((x - 860 - k * 40) / 170) ** 2) - k * 18) * S / S * 1) * 1
               for x in range(0, 1201, 6)]
        d.line([(a, b) for a, b in pts], fill=c, width=6 * S, joint="curve")
    mark(d, 80, 90, 120)
    label(d, (230, 100), "Enerlytix", 64)
    label(d, (230, 172), "Technologies, LLC", 34, MIST, False)
    label(d, (80, 300), "Intelligent Energy.", 62)
    label(d, (80, 372), "Advanced Analytics.", 62)
    label(d, (80, 444), "Sustainable Innovation.", 62)
    save(im, "og-image.png", W, H)

    for size, name in ((512, "logo-512.png"), (180, "apple-touch-icon.png"), (32, "favicon-32.png")):
        t = Image.new("RGB", (size * S, size * S), INK); td = ImageDraw.Draw(t)
        mark(td, size * .1 / 1, size * .1, size * .8) if False else None
        # scale mark into the tile
        mm = size * .74 / S * S
        mark(td, size * .13, size * .13, size * .74 * 1)
        t.resize((size, size), Image.LANCZOS).save(OUT / name)


LOGO = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" role="img" aria-label="Enerlytix">
<rect width="64" height="64" rx="14" fill="#08222F"/>
<rect x="12" y="13" width="34" height="8" rx="4" fill="#fff"/>
<rect x="12" y="28" width="24" height="8" rx="4" fill="#fff"/>
<rect x="12" y="43" width="34" height="8" rx="4" fill="#fff"/>
<circle cx="47" cy="32" r="5" fill="#F5A623"/></svg>'''

if __name__ == "__main__":
    for fn in (forecast, smartgrid, battery, ainet, social):
        fn()
    (OUT / "logo.svg").write_text(LOGO); (OUT / "favicon.svg").write_text(LOGO)
    print("images written to", OUT)

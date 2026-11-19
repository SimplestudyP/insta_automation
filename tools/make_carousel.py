import sys, json, os
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H = 1080, 1350
FONT_B = "/usr/share/fonts/opentype/inter/InterDisplay-Bold.otf"
FONT_S = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
RED = (214, 40, 40)
rng = np.random.default_rng(7)


def scene(p):
    """Original scene: lone figure on a road under a dark moon; shadow grows with p (0..1)."""
    y = np.linspace(0, 1, H)[:, None]
    x = np.linspace(0, 1, W)[None, :]
    base = np.zeros((H, W, 3), np.float32)
    # deep blue-black sky gradient
    base[..., 0] = 6 + 10 * (1 - y)
    base[..., 1] = 8 + 14 * (1 - y)
    base[..., 2] = 14 + 30 * (1 - y)
    img = Image.fromarray(base.clip(0, 255).astype(np.uint8))

    # moon glow (red-tinted) rising slightly with p
    glow = Image.new("RGB", (W, H), (0, 0, 0))
    gd = ImageDraw.Draw(glow)
    mx, my, mr = 760, int(760 - 90 * p), 150
    gd.ellipse([mx - mr, my - mr, mx + mr, my + mr], fill=(190, 34, 34))
    glow = glow.filter(ImageFilter.GaussianBlur(120))
    img = Image.fromarray(np.clip(np.asarray(img, np.float32) + np.asarray(glow, np.float32) * 1.3, 0, 255).astype(np.uint8))
    d = ImageDraw.Draw(img)
    d.ellipse([mx - mr, my - mr, mx + mr, my + mr], fill=(48, 12, 14))
    d.ellipse([mx - mr, my - mr, mx + mr, my + mr], outline=(215, 52, 52), width=4)

    # road in perspective
    horizon = 860
    vp = (540, horizon)
    d.polygon([(0, H), (W, H), (vp[0] + 40, horizon), (vp[0] - 40, horizon)], fill=(9, 9, 12))
    d.polygon([(380, H), (700, H), (vp[0] + 6, horizon), (vp[0] - 6, horizon)], fill=(14, 14, 18))
    for i in range(7):
        t0, t1 = i / 7, i / 7 + 0.07
        def pt(t, off):
            yy = horizon + (H - horizon) * (t ** 1.8)
            return vp[0] + off * (t ** 1.8), yy
        a, b = pt(t0, -6), pt(t1, -6)
        c, e = pt(t1, 6), pt(t0, 6)
        d.polygon([a, b, c, e], fill=(70, 62, 40))
    # distant treeline
    for i in range(60):
        tx = i * 19 + rng.integers(-6, 6)
        th = rng.integers(40, 130)
        d.polygon([(tx, horizon), (tx + 10, horizon - th), (tx + 20, horizon)], fill=(4, 6, 8))

    # fog
    fog = Image.new("L", (W, H), 0)
    fd = ImageDraw.Draw(fog)
    for _ in range(14):
        cx, cy = rng.integers(0, W), rng.integers(horizon - 120, horizon + 80)
        fd.ellipse([cx - 320, cy - 40, cx + 320, cy + 40], fill=int(rng.integers(50, 110)))
    fog = fog.filter(ImageFilter.GaussianBlur(60))
    img = Image.composite(Image.new("RGB", (W, H), (60, 66, 84)), img, fog.point(lambda v: int(v * 0.55)))
    d = ImageDraw.Draw(img)

    # figure: grows/moves forward with p
    s = 0.55 + 0.9 * p
    fx, fy = 470 + 20 * p, horizon + 30 + 230 * p
    fh = 330 * s
    def fig(draw, ox, oy, scale, col):
        hh = 330 * scale
        draw.ellipse([ox - 20 * scale, oy - hh, ox + 20 * scale, oy - hh + 44 * scale], fill=col)           # head
        draw.polygon([(ox - 38 * scale, oy - hh + 50 * scale), (ox + 38 * scale, oy - hh + 50 * scale),
                      (ox + 50 * scale, oy - hh * 0.35), (ox + 30 * scale, oy), (ox + 6 * scale, oy),
                      (ox, oy - hh * 0.3), (ox - 6 * scale, oy), (ox - 30 * scale, oy),
                      (ox - 50 * scale, oy - hh * 0.35)], fill=col)                                         # coat + legs

    # long shadow stretching toward viewer, darker with p
    shadow = Image.new("L", (W, H), 0)
    sd = ImageDraw.Draw(shadow)
    ln = 380 + 520 * p
    sd.polygon([(fx - 30 * s, fy), (fx + 30 * s, fy), (fx + 150 + 280 * p, fy + ln), (fx - 150 + 120 * p, fy + ln)], fill=190)
    shadow = shadow.filter(ImageFilter.GaussianBlur(14))
    img = Image.composite(Image.new("RGB", (W, H), (0, 0, 0)), img, shadow)
    d = ImageDraw.Draw(img)

    # red rim light behind the figure
    rim = Image.new("RGB", (W, H), (0, 0, 0))
    rd = ImageDraw.Draw(rim)
    fig(rd, fx, fy, s * 1.03, (160, 30, 30))
    rim = rim.filter(ImageFilter.GaussianBlur(10))
    img = Image.fromarray(np.clip(np.asarray(img, np.float32) + np.asarray(rim, np.float32) * 0.8, 0, 255).astype(np.uint8))
    d = ImageDraw.Draw(img)
    fig(d, fx, fy, s, (3, 3, 5))

    # grain + vignette
    arr = np.asarray(img, np.float32)
    arr += rng.normal(0, 4.5, arr.shape)
    vy = (y - 0.5) ** 2
    vx = (x - 0.5) ** 2
    vig = 1 - 1.6 * (vx + vy)
    arr *= np.clip(vig, 0.4, 1)[..., None]
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))


HERE = os.path.dirname(os.path.abspath(__file__))
SERIF_I = os.path.join(HERE, "fonts", "GreatVibes-Regular.ttf")   # calligraphy for emphasis words
FOOT_F = os.path.join(HERE, "fonts", "Allura-Regular.ttf")        # calligraphy for footer
SERIF_R = os.path.join(HERE, "fonts", "InstrumentSerif-Regular.ttf")
SIZES = {"s": 70, "m": 82, "l": 96, "xl": 112}


def tokenize(text):
    """Split text into (word, emphasised) tokens. Emphasis = [[word or phrase]]."""
    toks, i, emph = [], 0, False
    buf = ""
    while i < len(text):
        if text.startswith("[[", i):
            if buf.strip():
                toks += [(w, emph) for w in buf.split()]
            buf, emph, i = "", True, i + 2
        elif text.startswith("]]", i):
            if buf.strip():
                toks += [(w, emph) for w in buf.split()]
            buf, emph, i = "", False, i + 2
            while i < len(text) and text[i] in ".,!?;:" and toks:   # keep punctuation glued to the emphasised word
                toks[-1] = (toks[-1][0] + text[i], toks[-1][1])
                i += 1
        else:
            buf += text[i]
            i += 1
    if buf.strip():
        toks += [(w, emph) for w in buf.split()]
    return toks


def layout(draw, toks, base, maxw, accent):
    """Return lines of (word, font, colour, emphasised). Emphasis words use elegant italic serif, larger."""
    sans = ImageFont.truetype(FONT_B, base)
    serif = ImageFont.truetype(SERIF_I, int(base * 1.85))
    lines, cur, curw = [], [], 0
    space = draw.textlength(" ", font=sans)
    for w, em in toks:
        f = serif if em else sans
        wl = draw.textlength(w, font=f) + (26 if em else 0)
        if cur and curw + space + wl > maxw:
            lines.append(cur)
            cur, curw = [], 0
        col = RED if (w.strip(".,!?").lower() in accent) else (245, 245, 245)
        cur.append((w, f, col, em))
        curw += (space if len(cur) > 1 else 0) + wl
    lines.append(cur)
    return lines


def slide(idx, total, text, accent, handle, size="m", last=False):
    p = idx / (total - 1)
    img = scene(p)
    top = Image.new("RGB", (W, H), (0, 0, 0))
    mask = Image.linear_gradient("L").resize((W, H)).transpose(Image.FLIP_TOP_BOTTOM).point(lambda v: int(v * 0.85))
    img = Image.composite(top, img, mask)
    d = ImageDraw.Draw(img)
    base = SIZES.get(size, 82)
    if len(text) > 80:
        base = min(base, 70)
    lines = layout(d, tokenize(text), base, W - 180, accent)
    sans = ImageFont.truetype(FONT_B, base)
    space = d.textlength(" ", font=sans)
    y = 120 + base  # baseline of first line
    for li, ln in enumerate(lines):
        has_em = any(t[3] for t in ln)
        if has_em:
            y += int(base * (0.55 if li == 0 else 0.42))   # room for tall calligraphy ascenders
        x = 90
        for w, f, col, em in ln:
            if em:
                x += 13
            d.text((x, y), w, font=f, fill=col, anchor="ls")
            x += d.textlength(w, font=f) + space + (13 if em else 0)
        y += int(base * 1.32) + (int(base * 0.30) if has_em else 0)
    sf = ImageFont.truetype(FOOT_F, 66)
    if last:
        d.text((90, H - 74), "@" + handle.lower(), font=sf, fill=(235, 235, 235), anchor="ls")
        d.line([(90, H - 56), (560, H - 56)], fill=RED, width=3)
    else:
        d.text((90, H - 74), "the inner community", font=sf, fill=(235, 235, 235), anchor="ls")
        d.line([(90, H - 56), (480, H - 56)], fill=RED, width=3)
        d.text((W - 90, H - 74), "swipe", font=sf, fill=(235, 235, 235), anchor="rs")
    return img


if __name__ == "__main__":
    spec = json.load(open(sys.argv[1]))
    out = sys.argv[2]
    os.makedirs(out, exist_ok=True)
    n = len(spec["slides"])
    for i, s in enumerate(spec["slides"]):
        im = slide(i, n, s["text"], [a.lower().strip(".,") for a in s.get("accent", [])], spec["handle"], size=s.get("size", "m"), last=(i == n - 1))
        im.convert("RGB").save(os.path.join(out, f"slide_{i+1:02d}.jpg"), quality=92, optimize=True)
    print("done", n)

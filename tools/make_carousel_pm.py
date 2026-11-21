#!/usr/bin/env python3
"""Premium Minimal carousel renderer (1080x1350 JPEG slides) on top of photos.

Usage: python3 tools/make_carousel_pm.py posts/<date>/spec.json posts/<date>

Spec (JSON):
{
  "handle": "theinnercommunity",
  "hook_type": "...", "theme": "...", "experiment": "...",
  "slides": [
    {"text": "Someone [[hungrier]] is outworking you right now.",
     "image": "11-crane-hook",        # id from tools/photos.json (file in assets/photos/)
     "key": "italic",                  # italic (default) | sans | roman | box
     "size": "xl",                     # s | m | l | xl  (key word size)
     "pos": "top",                     # optional: top | mid | bottom (default from photos.json)
     "scene": "photo"}                 # photo (default) | blue (blue field, closing/statement)
  ]
}

Design language (Premium Minimal Edit design system): Inter 600 lead words, one key word
in Playfair Display italic (white on photos), one electric blue (#0b34ec field / #3d7bff on
dark), photo B-roll dimmed + vignette + moving-paper grain, square corners, no emoji.
Wrap the key word or phrase (1 to 2 words) in [[double brackets]]. Extra bracket pairs
become inline Playfair italic words inside the lead text.
"""
import base64
import html
import json
import re
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
W, H = 1080, 1350
SAFE_X = 96
FONTS = ROOT / "tools" / "fonts"
PHOTOS = ROOT / "assets" / "photos"
META = json.loads((ROOT / "tools" / "photos.json").read_text())

KEY_PX = {"s": 112, "m": 136, "l": 164, "xl": 196}
KEY_STYLE = {
    "italic": "font-family:'Playfair Display',serif;font-style:italic;font-weight:700;letter-spacing:-0.025em;line-height:0.9;",
    "roman": "font-family:'Playfair Display',serif;font-style:normal;font-weight:600;letter-spacing:-0.06em;line-height:0.9;",
    "sans": "font-family:'Inter',sans-serif;font-weight:800;letter-spacing:-0.045em;line-height:0.88;",
    "box": "font-family:'Playfair Display',serif;font-style:italic;font-weight:700;letter-spacing:-0.025em;line-height:0.95;",
}


def split_text(text):
    """Return (pre, key, post) where key is the first [[...]] phrase. Other pairs -> <em>."""
    m = re.search(r"\[\[(.+?)\]\]", text)
    if not m:
        return "", text.strip(), ""
    pre, key, post = text[: m.start()], m.group(1), text[m.end():]

    def inline(s):
        s = html.escape(s)
        return re.sub(r"\[\[(.+?)\]\]", r"<em>\1</em>", s)

    # punctuation that directly follows the key word belongs to the key word
    pm = re.match(r"^([.,;:!?\u2026\u201d\")]+)", post)
    if pm:
        key += pm.group(1)
        post = post[pm.end():]
    return inline(pre).strip(), html.escape(key), inline(post).strip()


def font_face_css():
    def b64(p):
        return base64.b64encode((FONTS / p).read_bytes()).decode()

    return f"""
@font-face{{font-family:'Inter';src:url(data:font/woff2;base64,{b64('Inter-Variable.woff2')}) format('woff2');font-weight:100 900;font-style:normal}}
@font-face{{font-family:'Playfair Display';src:url(data:font/woff2;base64,{b64('PlayfairDisplay-Variable.woff2')}) format('woff2');font-weight:400 900;font-style:normal}}
@font-face{{font-family:'Playfair Display';src:url(data:font/woff2;base64,{b64('PlayfairDisplay-Italic-Variable.woff2')}) format('woff2');font-weight:400 900;font-style:italic}}
"""


def slide_html(i, n, s, handle, fonts_css):
    scene = s.get("scene", "photo")
    pre, key, post = split_text(s["text"])
    kstyle = s.get("key", "italic")
    size = s.get("size", "l")
    key_px = KEY_PX.get(size, 164)
    img_id = s.get("image")
    meta = META.get(img_id, {}) if img_id else {}
    zone = s.get("pos") or meta.get("zone", "bottom")
    fx, fy = meta.get("fx", 50), meta.get("fy", 50)
    dim = meta.get("dim", 0.62)
    img_path = (PHOTOS / f"{img_id}.jpg") if img_id else None
    blue = scene == "blue"

    if blue:
        bg = f"""
<div class="blue"></div>
{f'<img class="duo" src="file://{img_path}" style="object-position:{fx}% {fy}%">' if img_path else ''}
<div class="blue-lift"></div>
<svg class="fibre" width="{W}" height="{H}"><filter id="f"><feTurbulence type="fractalNoise" baseFrequency="0.9 0.025" numOctaves="3" seed="{i * 7 + 3}"/><feColorMatrix values="0 0 0 0 0.55  0 0 0 0 0.68  0 0 0 0 1  0 0 0 1.4 -0.45"/></filter><rect width="100%" height="100%" filter="url(#f)"/></svg>
<div class="qmark">&ldquo;</div>
"""
        zone = "mid"
        tone = "on-blue"
    else:
        bg = f"""
<img class="photo" src="file://{img_path}" style="object-position:{fx}% {fy}%;filter:brightness({dim}) contrast(1.06) blur(1.4px)">
<div class="shade shade-{zone}"></div>
<div class="vig"></div>
<svg class="grain" width="{W}" height="{H}"><filter id="g"><feTurbulence type="fractalNoise" baseFrequency="0.85" numOctaves="2" seed="{i * 5 + 1}"/><feColorMatrix type="saturate" values="0"/></filter><rect width="100%" height="100%" filter="url(#g)"/></svg>
"""
        tone = "on-photo"

    pre_html = f'<div class="pre">{pre}</div>' if pre else ""
    post_html = f'<div class="post">{post}</div>' if post else ""
    key_html = f'<div class="key k-{kstyle}" id="key" style="font-size:{key_px}px;{KEY_STYLE.get(kstyle, KEY_STYLE["italic"])}"><span>{key}</span></div>'

    last = i == n - 1
    left_foot = f"@{handle}" if last else "the inner community"
    right_foot = (
        '<span class="swipe">SWIPE</span><svg width="64" height="14" viewBox="0 0 64 14"><path d="M0 7 H60 M54 1 L62 7 L54 13" stroke="#fff" stroke-width="3" fill="none"/></svg>'
        if i == 0
        else f'<span class="count">{i + 1:02d} / {n:02d}</span>'
    )

    return f"""<!doctype html><html><head><meta charset="utf-8"><style>
{fonts_css}
*{{margin:0;padding:0;box-sizing:border-box}}
html,body{{width:{W}px;height:{H}px;background:#0d0d0d;overflow:hidden}}
.stage{{position:relative;width:{W}px;height:{H}px;overflow:hidden;color:#fff;font-family:'Inter',sans-serif}}
.photo,.duo{{position:absolute;inset:-8px;width:{W + 16}px;height:{H + 16}px;object-fit:cover}}
.shade{{position:absolute;inset:0}}
.shade-top{{background:linear-gradient(180deg,rgba(0,0,0,.72) 0%,rgba(0,0,0,.45) 38%,rgba(0,0,0,0) 62%)}}
.shade-mid{{background:radial-gradient(ellipse 80% 40% at 50% 44%,rgba(0,0,0,.6),rgba(0,0,0,0) 100%)}}
.shade-bottom{{background:linear-gradient(0deg,rgba(0,0,0,.78) 0%,rgba(0,0,0,.5) 36%,rgba(0,0,0,0) 62%)}}
.vig{{position:absolute;inset:0;background:radial-gradient(ellipse 75% 70% at 50% 50%,rgba(0,0,0,0) 45%,rgba(0,0,0,.55) 100%)}}
.grain{{position:absolute;inset:0;opacity:.16;mix-blend-mode:overlay}}
.blue{{position:absolute;inset:0;background:#0b34ec}}
.duo{{filter:grayscale(1) contrast(1.25) brightness(1.7);mix-blend-mode:multiply;opacity:.7}}
.blue-lift{{position:absolute;inset:0;background:#1d27b6;mix-blend-mode:lighten;opacity:.9}}
.fibre{{position:absolute;inset:0;opacity:.28;mix-blend-mode:screen}}
.qmark{{position:absolute;left:0;right:0;top:120px;text-align:center;font-family:'Playfair Display',serif;font-style:italic;font-weight:800;font-size:260px;line-height:1;color:#fff}}
.wrap{{position:absolute;left:{SAFE_X}px;right:{SAFE_X}px;display:flex;justify-content:center}}
.wrap.top{{top:170px}}
.wrap.mid{{top:50%;transform:translateY(-50%)}}
.wrap.bottom{{bottom:250px;align-items:flex-end}}
.block{{display:flex;flex-direction:column;max-width:{W - 2 * SAFE_X}px}}
.pre,.post{{font-family:'Inter',sans-serif;font-weight:600;letter-spacing:-0.02em;line-height:1.04;text-shadow:0 2px 14px rgba(0,0,0,.38)}}
.pre{{align-self:flex-start;margin-bottom:8px;text-wrap:balance}}
.post{{align-self:flex-end;text-align:right;margin-top:8px;text-wrap:balance}}
.pre em,.post em{{font-family:'Playfair Display',serif;font-style:italic;font-weight:700;letter-spacing:-0.02em}}
.key{{align-self:center;text-align:center;white-space:nowrap;text-shadow:0 2px 14px rgba(0,0,0,.38)}}
.key.k-box span{{display:inline-block;background:#0b34ec;color:#fff;padding:6px 26px 14px;text-shadow:none}}
.on-blue .key,.on-blue .pre,.on-blue .post{{text-shadow:none}}
.foot{{position:absolute;left:{SAFE_X}px;right:{SAFE_X}px;bottom:78px;display:flex;justify-content:space-between;align-items:center}}
.brand{{font-family:'Playfair Display',serif;font-style:italic;font-weight:600;font-size:34px;letter-spacing:-0.01em;display:flex;align-items:center;gap:14px;text-shadow:0 2px 10px rgba(0,0,0,.5)}}
.brand i{{display:block;width:14px;height:14px;border-radius:50%;background:#3d7bff;box-shadow:0 0 18px rgba(61,123,255,.7)}}
.on-blue .brand i{{background:#fff;box-shadow:none}}
.swipe{{font-weight:800;font-size:26px;letter-spacing:.14em;margin-right:16px}}
.count{{font-weight:500;font-size:22px;letter-spacing:.14em;opacity:.8}}
.right{{display:flex;align-items:center;text-shadow:0 2px 10px rgba(0,0,0,.5)}}
</style></head><body><div class="stage {tone}">
{bg}
<div class="wrap {zone}"><div class="block" id="block">{pre_html}{key_html}{post_html}</div></div>
<div class="foot"><div class="brand"><i></i>{html.escape(left_foot)}</div><div class="right">{right_foot}</div></div>
</div>
<script>
(async()=>{{
  await document.fonts.ready;
  const key=document.getElementById('key'), block=document.getElementById('block');
  const pre=block.querySelector('.pre'), post=block.querySelector('.post');
  const maxW={W - 2 * SAFE_X};
  let k={key_px};
  // lead size: about .42 of key, clamped like the design system (64px vs 148-160px)
  const lead=()=>Math.max(46,Math.min(74,Math.round(k*0.42)));
  const apply=()=>{{key.style.fontSize=k+'px';[pre,post].forEach(e=>e&&(e.style.fontSize=lead()+'px'));}};
  apply();
  const widest=()=>Math.max(key.scrollWidth,pre?pre.scrollWidth:0,post?post.scrollWidth:0);
  let guard=0;
  while(key.scrollWidth>maxW && k>60 && guard++<80){{k-=4;apply();}}
  // limit the block height so it never grows into the footer
  guard=0;
  while(block.getBoundingClientRect().height>560 && k>60 && guard++<80){{k-=4;apply();}}
  document.body.dataset.ready='1';
}})();
</script></body></html>"""


def main():
    spec_path, out_dir = Path(sys.argv[1]), Path(sys.argv[2])
    out_dir.mkdir(parents=True, exist_ok=True)
    spec = json.loads(spec_path.read_text())
    slides = spec["slides"]
    handle = spec.get("handle", "theinnercommunity")
    fonts_css = font_face_css()
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": W, "height": H}, device_scale_factor=1)
        for i, s in enumerate(slides):
            tmp = out_dir / f".tmp_{i}.html"
            tmp.write_text(slide_html(i, len(slides), s, handle, fonts_css))
            page.goto(f"file://{tmp}")
            page.wait_for_function("document.body.dataset.ready==='1'")
            page.wait_for_timeout(150)
            page.screenshot(path=str(out_dir / f"slide_{i + 1:02d}.jpg"), type="jpeg", quality=92)
            tmp.unlink()
        browser.close()
    print("done", len(slides))


if __name__ == "__main__":
    main()

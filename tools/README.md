# Carousel tooling

## Current renderer: `make_carousel_pm.py` (from 2026-11-22)
Photo-based "Premium Minimal Edit" look on 1080x1350 slides, rendered with Playwright/Chromium.

    python3 tools/make_carousel_pm.py posts/<date>/spec.json posts/<date>

- Photos live in `assets/photos/<id>.jpg`; `tools/photos.json` gives each one a default text `zone` (top/mid/bottom), crop focus (`fx`, `fy` as % object-position), `dim` (brightness) and a `mood` note used to match lines to pictures.
- Fonts: Inter (lead words) and Playfair Display (italic key word), both in `tools/fonts/*.woff2`.
- Colour: white on photos, one electric blue (#0b34ec field, #3d7bff glow dot), no second hue, no emoji.
- Spec slide fields: `text` with the key phrase in `[[double brackets]]`, `image` (photo id), `key` = `italic` (default) | `sans` | `roman` | `box` (white on a blue highlight box), `size` = `s|m|l|xl` (key word size, auto-shrinks to fit), `pos` = `top|mid|bottom` (override), `scene` = `photo` (default) | `blue` (flat blue field with quote mark and duotone texture).
- Punctuation that follows the key phrase is attached to it automatically.

## Old renderer: `make_carousel.py` (2026-11-19 to 2026-11-21)
Illustrated figure, moon and road with Great Vibes calligraphy. Kept only as a fallback.

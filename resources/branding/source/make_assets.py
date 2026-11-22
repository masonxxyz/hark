"""Generate every Hark brand asset into the hark repos.

Requires: pip install resvg-py pillow, and the Geist font (OFL) for the
wordmark. Run from anywhere: python3 make_assets.py
"""
import io, os, sys, json, shutil, subprocess, tempfile
sys.path.insert(0, os.path.dirname(__file__))
import hark_logo as L
from resvg_py import svg_to_bytes
from PIL import Image, ImageDraw, ImageFont

# Paths: this file lives in <core>/resources/branding/source; the core repo is
# normally checked out as the hark-chromium submodule of hark-macos.
_HERE = os.path.dirname(os.path.abspath(__file__))
CORE = os.environ.get("HARK_CORE", os.path.abspath(os.path.join(_HERE, "../../..")))
MAC = os.environ.get("HARK_MACOS", os.path.dirname(CORE))
BR = os.path.join(CORE, "resources/branding")
TOP, BOTTOM = L.PALETTES["ember"]
MID = "#EF5638"
GLYPH_BBOX = (L.CX - L.HALF_SPAN - L.W / 2, L.CY - L.HALF_H - L.W / 2,
              L.CX + L.HALF_SPAN + L.W / 2, L.CY + L.HALF_H + L.W / 2)
HEADER = ("// Copyright 2026 The Hark Authors\n"
          "// You can use, redistribute, and/or modify this source code under\n"
          "// the terms of the GPL-3.0 license that can be found in the LICENSE file.\n\n")


def render(svg, w=None, h=None):
    im = Image.open(io.BytesIO(bytes(svg_to_bytes(svg_string=svg)))).convert("RGBA")
    if w and (im.width != w or im.height != h):
        im = im.resize((w, h), Image.LANCZOS)
    return im


def fit(box_w, box_h, pad):
    """scale/offset that fits the glyph bbox centred in a box."""
    gx0, gy0, gx1, gy1 = GLYPH_BBOX
    s = min((box_w - 2 * pad) / (gx1 - gx0), (box_h - 2 * pad) / (gy1 - gy0))
    ox = (box_w - (gx1 - gx0) * s) / 2 - gx0 * s
    oy = (box_h - (gy1 - gy0) * s) / 2 - gy0 * s
    return s, ox, oy


def glyph_svg(w, h, pad, fill):
    s, ox, oy = fit(w, h, pad)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
            f'viewBox="0 0 {w} {h}">{L.glyph_svg_paths(s, ox, oy, fill)}</svg>')


GS = 0.80  # glyph scale inside the app-icon squircle


def squircle_svg(size, inset, shadow=False, glyph_scale=GS):
    box = size - 2 * inset
    s = box / 256 * glyph_scale
    o = inset + (box - 256 * s) / 2
    rx = box * 0.2237
    filt = ('<filter id="sh" x="-20%" y="-20%" width="140%" height="140%">'
            f'<feDropShadow dx="0" dy="{size*0.012:.1f}" stdDeviation="{size*0.018:.1f}" '
            'flood-color="#000" flood-opacity="0.35"/></filter>') if shadow else ""
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 {size} {size}">'
        f'<defs><linearGradient id="g" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="{TOP}"/><stop offset="1" stop-color="{BOTTOM}"/></linearGradient>'
        f'<linearGradient id="hl" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="#fff" stop-opacity="0.22"/><stop offset="0.5" stop-color="#fff" stop-opacity="0"/></linearGradient>'
        f'{filt}</defs>'
        f'<g{" filter=\"url(#sh)\"" if shadow else ""}>'
        f'<rect x="{inset}" y="{inset}" width="{box}" height="{box}" rx="{rx}" fill="url(#g)"/></g>'
        f'<rect x="{inset}" y="{inset}" width="{box}" height="{box}" rx="{rx}" fill="url(#hl)"/>'
        f'{L.glyph_svg_paths(s, o, o, "#FFFFFF")}</svg>')


def wordmark(h, color):
    """mark + 'Hark' wordmark, Helium-style 140x32 proportions."""
    W = int(h * 140 / 32)
    font = ImageFont.truetype(os.path.expanduser("~/Library/Fonts/Geist-SemiBold.ttf"), int(h * 0.86))
    canvas = Image.new("RGBA", (W, h), (0, 0, 0, 0))
    mark = render(glyph_svg(h, h, h * 0.06, color))
    canvas.alpha_composite(mark, (0, 0))
    d = ImageDraw.Draw(canvas)
    x = int(h * 1.18)
    bbox = d.textbbox((0, 0), "Hark", font=font)
    y = (h - (bbox[3] - bbox[1])) / 2 - bbox[1]
    d.text((x, y), "Hark", font=font, fill=color)
    return canvas


def icon_file(lines):
    return HEADER + "\n".join(lines) + "\n"


def main():
    os.makedirs(BR + "/app_icon", exist_ok=True)
    # --- core: app icon sources -------------------------------------------
    raw = render(squircle_svg(1024, 1024 * 0.02))
    raw.save(BR + "/app_icon/raw.png")
    # document ("file") icon: page with folded corner + small app icon
    page = (f'<svg xmlns="http://www.w3.org/2000/svg" width="512" height="512" viewBox="0 0 512 512">'
            '<defs><filter id="s"><feDropShadow dx="0" dy="4" stdDeviation="6" flood-opacity="0.25"/></filter></defs>'
            '<path filter="url(#s)" d="M100 30h200l112 112v320a20 20 0 0 1-20 20H100a20 20 0 0 1-20-20V50a20 20 0 0 1 20-20z" fill="#F7F7F8"/>'
            '<path d="M300 30v92a20 20 0 0 0 20 20h92z" fill="#E4E4E7"/></svg>')
    f = render(page)
    small = render(squircle_svg(232, 0))
    f.alpha_composite(small, (140, 200))
    f.save(BR + "/app_icon/file.png")
    # --- core: product logo svg / vector icons -----------------------------
    with open(BR + "/product_logo.svg", "w") as fh:
        s = 0.80; o = (256 - 256 * s) / 2
        fh.write(f'<svg width="256" height="256" viewBox="0 0 256 256" fill="none" xmlns="http://www.w3.org/2000/svg">'
                 f'<defs><linearGradient id="g" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{TOP}"/>'
                 f'<stop offset="1" stop-color="{BOTTOM}"/></linearGradient></defs>'
                 f'<rect width="256" height="256" rx="67" fill="url(#g)"/>{L.glyph_svg_paths(s, o, o, "#FFFFFF")}</svg>\n')
    s, ox, oy = fit(56, 56, 1.5)
    with open(BR + "/product_logo.icon", "w") as fh:
        fh.write(icon_file(["CANVAS_DIMENSIONS, 56,", "FILL_RULE_NONZERO,"] + L.icon_commands(s, ox, oy)))
    r, g, b = (int(MID[i:i + 2], 16) for i in (1, 3, 5))
    color_lines = ["CANVAS_DIMENSIONS, 256,", "NEW_PATH,",
                   f"PATH_COLOR_ARGB, 0xFF, 0x{r:02X}, 0x{g:02X}, 0x{b:02X},",
                   "ROUND_RECT, 0, 0, 256, 256, 67,"]
    s = 0.80; o = (256 - 256 * s) / 2
    for ln in L.icon_commands(s, o, o):
        color_lines.append(ln)
        if ln == "NEW_PATH,":
            color_lines.append("PATH_COLOR_ARGB, 0xFF, 0xFF, 0xFF, 0xFF,")
    with open(BR + "/product_logo_color.icon", "w") as fh:
        fh.write(icon_file(color_lines))
    # --- core: wordmarks + mono -------------------------------------------
    wordmark(32, "#000000").save(BR + "/product_logo.png")
    wordmark(64, "#000000").save(BR + "/product_logo_200.png")
    wordmark(32, "#FFFFFF").save(BR + "/product_logo_white.png")
    wordmark(64, "#FFFFFF").save(BR + "/product_logo_white_200.png")
    render(glyph_svg(22, 22, 2, "#3C4043")).save(BR + "/product_logo_22_mono.png")
    for sz in (16, 32):
        render(glyph_svg(sz, sz, sz * 0.09, "#3C4043")).save(
            os.path.join(CORE, f"resources/favicons/favicon_ntp_{sz}.png"))
    # --- macOS: Icon Composer + legacy bitmaps -----------------------------
    A = os.path.join(MAC, "resources/assets")
    with open(os.path.join(A, "AppIcon.icon/Assets/logo.svg"), "w") as fh:
        fh.write(glyph_svg(512, 512, 0, "currentColor").replace(
            '<svg ', '<svg fill="none" ') + "\n")
    render(squircle_svg(1024, 100, shadow=True)).save(os.path.join(A, "legacy.png"))
    render(squircle_svg(512, 512 * 0.02)).save(os.path.join(A, "legacy_crop.png"))
    # DMG background: soft ember glow with down chevrons
    dmg = ('<svg xmlns="http://www.w3.org/2000/svg" width="700" height="1036" viewBox="0 0 700 1036">'
           f'<defs><radialGradient id="r" cx="0.5" cy="0.48" r="0.5"><stop offset="0" stop-color="{TOP}" stop-opacity="0.85"/>'
           f'<stop offset="0.55" stop-color="{BOTTOM}" stop-opacity="0.35"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></radialGradient></defs>'
           '<rect width="700" height="1036" fill="#fff"/><rect width="700" height="1036" fill="url(#r)"/>'
           + "".join(f'<path d="M327 {y} l23 18 l23 -18" stroke="#fff" stroke-opacity="0.9" stroke-width="5" '
                     'fill="none" stroke-linecap="round" stroke-linejoin="round"/>' for y in (450, 490, 530))
           + '</svg>')
    render(dmg).save(os.path.join(MAC, "resources/dmg_background.png"))
    print("assets written to", CORE, "and", MAC)


if __name__ == "__main__":
    main()

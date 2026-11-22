"""Hark logo geometry: one source of truth for SVG, Chromium .icon and PNG.

The mark is an "H" whose stems bow outward like sound waves: (-)
Everything is expressed as filled outlines (no strokes) so the same paths
work in SVG, Chromium vector icons and Icon Composer.
"""
import math

# Glyph parameters on a 256x256 design canvas, centred on (128, 128).
CX = CY = 128.0
HALF_SPAN = 64.0   # half the distance between the stems' midpoints
HALF_H = 66.0      # half the stem height (centre-line)
BOW = 18.0         # how far the stem midpoints bow outward vs their ends
W = 32.0           # stroke weight
BAR_W = 28.0       # crossbar weight

PALETTES = {
    "ember": ("#FF7A45", "#E0342B"),
    "violet": ("#8B5CF6", "#4C1D95"),
    "teal": ("#2DD4BF", "#0F5F5A"),
    "ink": ("#3A3F4B", "#0E1014"),
}


def _stem(side):
    """Outline of one bowed stem with round caps. side=-1 left, +1 right."""
    xm = CX + side * HALF_SPAN            # stem midpoint (furthest out)
    r = (BOW ** 2 + HALF_H ** 2) / (2 * BOW)
    ccx = xm - side * r                   # circle centre lies toward the middle
    phi = math.asin(HALF_H / r)           # half the swept angle

    def pt(rad, ang):
        # ang measured from the outward horizontal direction
        return (ccx + side * rad * math.cos(ang), CY + rad * math.sin(ang))

    ro, ri, cap = r + W / 2, r - W / 2, W / 2
    top_o, bot_o = pt(ro, -phi), pt(ro, phi)
    top_i, bot_i = pt(ri, -phi), pt(ri, phi)
    # Sweep flags: for the left stem the outer arc goes top->bottom
    # counter-clockwise in SVG's y-down space.
    s_outer = 0 if side < 0 else 1
    s_inner = 1 - s_outer
    return [
        ("M", top_o),
        ("A", (ro, ro, 0, 0, s_outer), bot_o),
        ("A", (cap, cap, 0, 0, s_outer), bot_i),
        ("A", (ri, ri, 0, 0, s_inner), top_i),
        ("A", (cap, cap, 0, 0, s_outer), top_o),
        ("Z",),
    ]


def _bar():
    x0, x1 = CX - HALF_SPAN, CX + HALF_SPAN
    y0, y1 = CY - BAR_W / 2, CY + BAR_W / 2
    return [("M", (x0, y0)), ("L", (x1, y0)), ("L", (x1, y1)),
            ("L", (x0, y1)), ("Z",)]


def shapes():
    return [_stem(-1), _bar(), _stem(1)]


def _tx(p, scale, ox, oy):
    return (p[0] * scale + ox, p[1] * scale + oy)


def svg_path(shape, scale=1.0, ox=0.0, oy=0.0):
    out = []
    for cmd in shape:
        if cmd[0] in "ML":
            x, y = _tx(cmd[1], scale, ox, oy)
            out.append(f"{cmd[0]}{x:.2f} {y:.2f}")
        elif cmd[0] == "A":
            rx, ry, rot, large, sweep = cmd[1]
            x, y = _tx(cmd[2], scale, ox, oy)
            out.append(f"A{rx*scale:.2f} {ry*scale:.2f} {rot} {large} {sweep} {x:.2f} {y:.2f}")
        else:
            out.append("Z")
    return "".join(out)


def glyph_svg_paths(scale=1.0, ox=0.0, oy=0.0, fill="currentColor"):
    return "".join(f'<path d="{svg_path(s, scale, ox, oy)}" fill="{fill}"/>'
                   for s in shapes())


def _f(v):
    v = round(v, 2)
    return str(int(v)) if v == int(v) else f"{v}f"


def icon_commands(scale=1.0, ox=0.0, oy=0.0):
    """Chromium vector-icon commands (one NEW_PATH per shape)."""
    lines = []
    for shape in shapes():
        lines.append("NEW_PATH,")
        for cmd in shape:
            if cmd[0] == "M":
                x, y = _tx(cmd[1], scale, ox, oy)
                lines.append(f"MOVE_TO, {_f(x)}, {_f(y)},")
            elif cmd[0] == "L":
                x, y = _tx(cmd[1], scale, ox, oy)
                lines.append(f"LINE_TO, {_f(x)}, {_f(y)},")
            elif cmd[0] == "A":
                rx, ry, rot, large, sweep = cmd[1]
                x, y = _tx(cmd[2], scale, ox, oy)
                lines.append(f"ARC_TO, {_f(rx*scale)}, {_f(ry*scale)}, {rot}, "
                             f"{large}, {sweep}, {_f(x)}, {_f(y)},")
            else:
                lines.append("CLOSE,")
    return lines


def app_icon_svg(size=1024, palette="ember", margin=0.0, radius=0.2237,
                 glyph_scale=1.0, flat=False):
    """Full-colour app icon: gradient squircle + white glyph."""
    top, bottom = PALETTES[palette]
    inset = size * margin
    box = size - 2 * inset
    rx = box * radius
    s = box / 256 * glyph_scale
    o = inset + (box - 256 * s) / 2
    fill = top if flat else "url(#g)"
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" '
        f'viewBox="0 0 {size} {size}">'
        f'<defs><linearGradient id="g" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="{top}"/><stop offset="1" stop-color="{bottom}"/>'
        f'</linearGradient></defs>'
        f'<rect x="{inset}" y="{inset}" width="{box}" height="{box}" rx="{rx}" fill="{fill}"/>'
        f'{glyph_svg_paths(s, o, o, "#FFFFFF")}</svg>'
    )

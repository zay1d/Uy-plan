"""Упрощённые планы этажей (для расстановки мебели) из чертежей КЖ 9.1 / 9.2.

Геометрия стен снята с векторов исходных PDF (source/*.pdf), переведена в мм
в системе осей: ось 1 = X 0, ось 9 = X 29700, ось А = Y 0, ось Д = Y 13600.
Сантехника и лестницы копируются из PDF как есть.

Запуск: python3 tools/make_plan.py  ->  plan/etazh-1.svg, plan/etazh-2.svg
"""
import math
import os
import pdfplumber

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = {1: os.path.join(ROOT, "source", "9.1-kirpich-0.000.pdf"),
       2: os.path.join(ROOT, "source", "9.2-kirpich-3.300.pdf")}
OUT = os.path.join(ROOT, "plan")

# PDF pt -> мм (по осевым линиям чертежа)
AX1, AX9, AXA = 96.84, 692.04, 474.2
K = 29700 / (AX9 - AX1)


def to_mm(x, top):
    return (x - AX1) * K, (AXA - top) * K


# ---------------------------------------------------------------- модель
# Прямоугольник: (x0, x1, y0, y1). Проёмы окон: (x0, x1, y0, y1) поверх стены.
EXT = []      # наружные / несущие стены (кирпич)
PART = []     # перегородки
COL = []      # отдельные колонны
WIN = []      # окна / витражи (ориентация определяется по форме)
OPEN = []     # дверные проёмы (для подписи ширины): (x, y, ширина, 'h'|'v')
ROOMS = []    # (название, [прямоугольники площади], (размер-прямоугольник), (lx, ly))
EXTRA = []    # прочие svg-элементы


def wall(lst, x0, x1, y0, y1, gaps=(), axis=None):
    """Стена с вырезанными проёмами gaps (по длинной стороне)."""
    if axis is None:
        axis = "h" if (x1 - x0) >= (y1 - y0) else "v"
    a0, a1 = (x0, x1) if axis == "h" else (y0, y1)
    cur = a0
    for g0, g1 in sorted(gaps):
        if g0 > cur:
            lst.append((x0, x1, cur, g0) if axis == "v" else (cur, g0, y0, y1))
        cur = g1
    if cur < a1:
        lst.append((x0, x1, cur, a1) if axis == "v" else (cur, a1, y0, y1))


def common_shell(floor):
    # ось 1 и ось 9 (глухие стены по границе участка)
    wall(EXT, -205, 200, -200, 13800, axis="v")
    wall(EXT, 29500, 29905, -200, 13800, axis="v")
    # ось А (низ крыльев), окна 2000
    wall(EXT, -205, 4600, -200, 200)
    wall(EXT, 25100, 29905, -200, 200)
    WIN.extend([(1200, 3200, -200, 200), (26500, 28500, -200, 200)])
    # ось Д (верх крыльев)
    wall(EXT, -205, 4450, 13400, 13800)
    wall(EXT, 25250, 29905, 13400, 13800)
    # ось 2 и ось 8 (внутренние стены крыльев)
    top = 4600 if floor == 1 else 4975
    wall(EXT, 4200, 4600, -200, top, axis="v")
    wall(EXT, 25100, 25500, -200, top, axis="v")
    wall(EXT, 4200, 4600, 12000, 13800, axis="v")
    wall(EXT, 25100, 25500, 12000, 13800, axis="v")
    WIN.extend([(4200, 4600, 12400, 13400), (25100, 25500, 12400, 13400)])
    # колонны у витражей (ось Б / оси 3 и 7)
    COL.extend([(6850, 7250, 4200, 4600), (22450, 22850, 4200, 4600)])
    # ось Г
    gl = [(4850, 5750)] if floor == 1 else []
    gr = [(23950, 24850)] if floor == 1 else []
    wall(EXT, 4600, 14600, 12000, 12400, gl)
    wall(EXT, 14600, 25100, 12000, 12400, gr)
    WIN.extend([(9000, 9750, 12000, 12400), (11645, 13645, 12000, 12400),
                (15550, 17550, 12000, 12400), (19450, 20195, 12000, 12400)])
    if floor == 1:
        OPEN.extend([(5300, 12200, 900, "h"), (24400, 12200, 900, "h")])
    # ось В (окна во двор)
    if floor == 1:
        wall(EXT, 4200, 4850, 6600, 7000)
        wall(EXT, 6345, 14600, 6600, 7000)
        wall(EXT, 14600, 23355, 6600, 7000)
        wall(EXT, 24850, 25500, 6600, 7000)
        OPEN.extend([(5600, 6800, 1495, "h"), (24100, 6800, 1495, "h")])
    else:
        wall(EXT, 6850, 14600, 6600, 7000)
        wall(EXT, 14600, 22850, 6600, 7000)
    WIN.extend([(7625, 9625, 6600, 7000), (11645, 13645, 6600, 7000),
                (15550, 17550, 6600, 7000), (19575, 21575, 6600, 7000)])
    # центральная стена (ось 5)
    wall(EXT, 14475, 14725, 6600, 13970 if floor == 1 else 12000, axis="v")


def floor1():
    common_shell(1)
    # тамбуры-витражи (оси 2-3 и 7-8 между Б и В): двери по 900
    for x in (4365, 7020, 22620, 25270):
        WIN.append((x, x + 65, 4600, 5150))
        WIN.append((x, x + 65, 6050, 6600))
    WIN.extend([(4600, 6850, 4370, 4430), (22850, 25100, 4370, 4430)])
    OPEN.extend([(4400, 5600, 900, "v"), (7050, 5600, 900, "v"),
                 (22650, 5600, 900, "v"), (25300, 5600, 900, "v")])
    # левая половина
    wall(PART, 8495, 8750, 8400, 12000, axis="v")            # лестница | с/у
    wall(PART, 8750, 10645, 8800, 9050, [(9400, 10195)])     # низ с/у
    wall(PART, 8750, 10645, 10080, 10195)                    # перегородка в с/у
    wall(EXT, 10645, 10900, 7000, 12000, [(7250, 8150)], axis="v")
    OPEN.extend([(9800, 8925, 795, "h"), (10770, 7700, 900, "v")])
    # правая половина
    wall(PART, 20950, 21195, 8400, 12000, axis="v")
    wall(PART, 18550, 20950, 8800, 9050, [(19000, 19800)])
    wall(PART, 18550, 20950, 10080, 10195)
    wall(EXT, 18300, 18550, 7000, 12000, [(7250, 8150)], axis="v")
    OPEN.extend([(19400, 8925, 800, "h"), (18425, 7700, 900, "v")])
    # внутренние дворики Д-Г: стенки возможной котельной
    wall(EXT, 10495, 10750, 12400, 13990, [(12525, 13270)], axis="v")
    wall(EXT, 18450, 18700, 12400, 13990, [(12525, 13270)], axis="v")
    OPEN.extend([(10620, 12900, 745, "v"), (18575, 12900, 745, "v")])

    R = ROOMS
    R.append(("Крыло|кирпичных перегородок нет", [(200, 4200, 200, 13400)], (200, 4200, 200, 13400), (2200, 9800)))
    R.append(("Крыло|кирпичных перегородок нет", [(25500, 29500, 200, 13400)], (25500, 29500, 200, 13400), (27500, 9800)))
    R.append(("Тамбур (витраж)", [(4430, 7020, 4430, 6600)], (4430, 7020, 4430, 6600), (5725, 5300)))
    R.append(("Тамбур (витраж)", [(22680, 25270, 4430, 6600)], (22680, 25270, 4430, 6600), (23975, 5300)))
    R.append(("Холл", [(4600, 10645, 7000, 8150), (8750, 10645, 8150, 8800)], None, (7000, 7600)))
    R.append(("Холл", [(18550, 25100, 7000, 8150), (18550, 20950, 8150, 8800)], None, (22600, 7600)))
    R.append(("Лестница", [(4600, 8495, 8150, 12000)], None, (6550, 10500)))
    R.append(("Лестница", [(21195, 25100, 8150, 12000)], None, (23150, 10500)))
    R.append(("С/у (ванна)", [(8750, 10645, 10195, 12000)], (8750, 10645, 10195, 12000), (9700, 11100)))
    R.append(("С/у", [(8750, 10645, 9050, 10080)], (8750, 10645, 9050, 10080), (9700, 9560)))
    R.append(("С/у (ванна)", [(18550, 20950, 10195, 12000)], (18550, 20950, 10195, 12000), (19750, 11100)))
    R.append(("С/у", [(18550, 20950, 9050, 10080)], (18550, 20950, 9050, 10080), (19750, 9560)))
    R.append(("Комната", [(10900, 14475, 7000, 12000)], (10900, 14475, 7000, 12000), (12690, 9700)))
    R.append(("Комната", [(14725, 18300, 7000, 12000)], (14725, 18300, 7000, 12000), (16510, 9700)))
    R.append(("Внутр. дворик (открыт)", [], None, (7550, 13150)))
    R.append(("Внутр. дворик (открыт)", [], None, (21650, 13150)))
    R.append(("Дворик / котельная", [], None, (12600, 13150)))
    R.append(("Дворик / котельная", [], None, (16600, 13150)))
    R.append(("Двор (открытый)", [], None, (14850, 3000)))


def floor2():
    common_shell(2)
    # витражи над тамбурами
    WIN.extend([(4600, 6850, 4345, 4450), (22850, 25100, 4345, 4450),
                (7000, 7095, 4600, 6600), (22600, 22700, 4600, 6600)])
    # левая половина
    wall(EXT, 4345, 4600, 8150, 12000, axis="v")              # стена лестницы
    wall(PART, 8495, 8750, 9100, 12000, axis="v")
    COL.append((8495, 8750, 8150, 8280))
    wall(PART, 8750, 11150, 9180, 9300, [(9495, 10400)])      # низ общего с/у
    wall(EXT, 11150, 11400, 7000, 12000, [(7250, 8150)], axis="v")
    OPEN.extend([(9950, 9240, 905, "h"), (11275, 7700, 900, "v")])
    # крыло: перегородки
    wall(PART, 200, 4200, 4855, 4975, [(1880, 2780), (3200, 4095)])
    wall(PART, 2880, 3000, 4975, 8400, [(7240, 7990)], axis="v")
    wall(PART, 200, 2880, 6880, 7000)
    wall(PART, 200, 4345, 8400, 8520, [(3200, 4095)])
    OPEN.extend([(2330, 4915, 900, "h"), (3650, 4915, 895, "h"),
                 (2940, 7615, 750, "v"), (3650, 8460, 895, "h")])
    # правая половина
    wall(EXT, 25100, 25355, 8150, 12000, axis="v")
    wall(PART, 20950, 21195, 8400, 12000, axis="v")
    wall(PART, 18050, 20950, 9180, 9300, [(18800, 19700)])
    wall(EXT, 17800, 18050, 7000, 12000, [(7250, 8150)], axis="v")
    OPEN.extend([(19250, 9240, 900, "h"), (17925, 7700, 900, "v")])
    wall(PART, 25500, 29500, 4855, 4975, [(25600, 26500), (26920, 27820)])
    wall(PART, 26700, 26820, 4975, 8400, [(7240, 7990)], axis="v")
    wall(PART, 26820, 29500, 6880, 7000)
    wall(PART, 25355, 29500, 8400, 8520, [(25600, 26500)])
    OPEN.extend([(27370, 4915, 900, "h"), (26050, 4915, 900, "h"),
                 (26760, 7615, 750, "v"), (26050, 8460, 900, "h")])
    # кровля над двориками 4-5 / 5-6
    for x0, x1 in ((10505, 14475), (14725, 18700)):
        EXTRA.append(("roof", (x0, x1, 12400, 13550)))

    R = ROOMS
    R.append(("Комната (родители)", [(200, 4200, 200, 4855)], (200, 4200, 200, 4855), (2200, 2700)))
    R.append(("Комната (родители)", [(25500, 29500, 200, 4855)], (25500, 29500, 200, 4855), (27500, 2700)))
    R.append(("С/у", [(200, 2880, 4975, 6880)], (200, 2880, 4975, 6880), (1540, 5700)))
    R.append(("С/у", [(26820, 29500, 4975, 6880)], (26820, 29500, 4975, 6880), (28160, 5700)))
    R.append(("Кладовая", [(200, 2880, 7000, 8400)], (200, 2880, 7000, 8400), (1540, 7700)))
    R.append(("Кладовая", [(26820, 29500, 7000, 8400)], (26820, 29500, 7000, 8400), (28160, 7700)))
    R.append(("Детская", [(200, 4345, 8520, 12000), (200, 4200, 12000, 13400)], (200, 4200, 8520, 13400), (2200, 10600)))
    R.append(("Детская", [(25355, 29500, 8520, 12000), (25500, 29500, 12000, 13400)], (25500, 29500, 8520, 13400), (27500, 10600)))
    R.append(("Холл", [(3000, 4200, 4975, 8400), (4200, 7000, 4450, 8150), (7000, 8750, 7000, 8150), (8750, 11150, 7000, 9180)], None, (5600, 6000)))
    R.append(("Холл", [(25500, 26700, 4975, 8400), (22700, 25500, 4450, 8150), (21195, 22700, 7000, 8150), (18050, 21195, 7000, 9180)], None, (24100, 6000)))
    R.append(("Лестница", [(4600, 8495, 8150, 12000)], None, (6550, 10500)))
    R.append(("Лестница", [(21195, 25100, 8150, 12000)], None, (23150, 10500)))
    R.append(("С/у общий", [(8750, 11150, 9300, 12000)], (8750, 11150, 9300, 12000), (9950, 10900)))
    R.append(("С/у общий", [(18050, 20950, 9300, 12000)], (18050, 20950, 9300, 12000), (19500, 10900)))
    R.append(("Детская", [(11400, 14475, 7000, 12000)], (11400, 14475, 7000, 12000), (12940, 9700)))
    R.append(("Детская", [(14725, 17800, 7000, 12000)], (14725, 17800, 7000, 12000), (16260, 9700)))
    R.append(("Внутр. дворик (открыт)", [], None, (7550, 13150)))
    R.append(("Внутр. дворик (открыт)", [], None, (21650, 13150)))
    R.append(("кровля 1 эт.", [], None, (12500, 13000)))
    R.append(("кровля 1 эт.", [], None, (16700, 13000)))


# ---------------------------------------------------------- копия из PDF
BLUE = (0.0, 0.0, 1.0)
LBLUE = (0.49804, 0.49804, 1.0)


def inside(pts, box):
    x0, x1, y0, y1 = box
    return all(x0 - 20 <= x <= x1 + 20 and y0 - 20 <= y <= y1 + 20 for x, y in pts)


def pdf_symbols(floor, stair_boxes, fixture_boxes):
    page = pdfplumber.open(SRC[floor]).pages[0]
    out = []
    for o in page.lines + page.curves + page.rects:
        col = tuple(o.get("stroking_color") or ())
        if o["object_type"] == "rect":
            pts = [(o["x0"], o["top"]), (o["x1"], o["top"]), (o["x1"], o["bottom"]),
                   (o["x0"], o["bottom"]), (o["x0"], o["top"])]
        else:
            pts = o.get("pts") or []
        pts = [to_mm(x, y) for x, y in pts]
        if len(pts) < 2:
            continue
        if col == LBLUE and any(inside(pts, b) for b in stair_boxes):
            out.append(("stair", pts))
        elif col == BLUE and any(inside(pts, b) for b in fixture_boxes):
            xs = [p[0] for p in pts]
            ys = [p[1] for p in pts]
            w, h = max(xs) - min(xs), max(ys) - min(ys)
            if len(pts) == 2 and w > 60 and h > 60:
                continue          # выноски-подписи сердечников
            if max(w, h) > 1900:
                continue          # перегородки (рисуются моделью)
            if o["object_type"] == "rect" and min(w, h) > 90 and max(w, h) > 700:
                continue
            out.append(("fix", pts))
    return out


# ------------------------------------------------------------------- SVG
VB = (-1400, -2600, 31300 + 1400, 17200)   # x0, y0(низ), x1, y1(верх) в мм


def sx(x):
    return x - VB[0]


def sy(y):
    return VB[3] - y


def rect_svg(r, cls):
    x0, x1, y0, y1 = r
    return f'<rect class="{cls}" x="{sx(x0):.0f}" y="{sy(y1):.0f}" width="{x1 - x0:.0f}" height="{y1 - y0:.0f}"/>'


def cm(v):
    return f"{round(v / 10):d}"


def dim_h(x0, x1, y, label=None, cls="dim"):
    t = label or cm(x1 - x0)
    a = 90
    return (f'<g class="{cls}"><line x1="{sx(x0)}" y1="{sy(y)}" x2="{sx(x1)}" y2="{sy(y)}"/>'
            f'<line x1="{sx(x0) - a}" y1="{sy(y) + a}" x2="{sx(x0) + a}" y2="{sy(y) - a}"/>'
            f'<line x1="{sx(x1) - a}" y1="{sy(y) + a}" x2="{sx(x1) + a}" y2="{sy(y) - a}"/>'
            f'<text x="{sx((x0 + x1) / 2)}" y="{sy(y) - 70}" text-anchor="middle">{t}</text></g>')


def dim_v(x, y0, y1, label=None, cls="dim"):
    t = label or cm(y1 - y0)
    a = 90
    cx, cy = sx(x) - 70, sy((y0 + y1) / 2)
    return (f'<g class="{cls}"><line x1="{sx(x)}" y1="{sy(y0)}" x2="{sx(x)}" y2="{sy(y1)}"/>'
            f'<line x1="{sx(x) - a}" y1="{sy(y0) + a}" x2="{sx(x) + a}" y2="{sy(y0) - a}"/>'
            f'<line x1="{sx(x) - a}" y1="{sy(y1) + a}" x2="{sx(x) + a}" y2="{sy(y1) - a}"/>'
            f'<text x="{cx}" y="{cy}" text-anchor="middle" transform="rotate(-90 {cx} {cy})">{t}</text></g>')


def area(rs):
    return sum((x1 - x0) * (y1 - y0) for x0, x1, y0, y1 in rs) / 1e6


def build(floor):
    for lst in (EXT, PART, COL, WIN, OPEN, ROOMS, EXTRA):
        lst.clear()
    (floor1 if floor == 1 else floor2)()

    stairs = [(4600, 8495, 8150, 12000), (21195, 25100, 8150, 12000)]
    if floor == 1:
        fixtures = [(8750, 10645, 9050, 12000), (18550, 20950, 9050, 12000)]
    else:
        fixtures = [(8750, 11150, 9300, 12000), (18050, 20950, 9300, 12000),
                    (200, 2880, 4975, 6880), (26820, 29500, 4975, 6880)]
    syms = pdf_symbols(floor, stairs, fixtures)

    W, H = VB[2] - VB[0], VB[3] - VB[1]
    o = []
    o.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
             f'width="{W / 100}mm" height="{H / 100}mm" font-family="DejaVu Sans, Arial, sans-serif">')
    o.append("""<style>
  .bg{fill:#fff}
  .grid line{stroke:#d9e3ec;stroke-width:8}
  .yard{fill:#f2f6ef}
  .room{fill:#fffdf8}
  .roof{fill:url(#roofp);stroke:#b9b9b9;stroke-width:12}
  .ext{fill:#3a3a3a}
  .part{fill:#7d7d7d}
  .col{fill:#3a3a3a}
  .win{fill:#fff;stroke:#2f8fd8;stroke-width:14}
  .winl{stroke:#2f8fd8;stroke-width:14}
  .stair{fill:none;stroke:#9a9a9a;stroke-width:10}
  .fix{fill:none;stroke:#5a6f8c;stroke-width:12}
  .fence{fill:none;stroke:#c98a3a;stroke-width:20;stroke-dasharray:160 90}
  .name{font-size:300px;font-weight:700;fill:#222}
  .sub{font-size:230px;fill:#444}
  .small{font-size:190px;fill:#666}
  .dim line{stroke:#c0392b;stroke-width:14}
  .dim text{font-size:220px;fill:#c0392b;font-weight:700}
  .odim line{stroke:#2f8fd8;stroke-width:10}
  .odim text{font-size:170px;fill:#2f8fd8}
  .ddim text{font-size:170px;fill:#8e44ad}
  .name,.sub,.small,.dim text{paint-order:stroke;stroke:#fff;stroke-width:45px;stroke-linejoin:round}
  .title{font-size:520px;font-weight:700;fill:#111}
  .note{font-size:240px;fill:#555}
</style>
<defs><pattern id="roofp" width="160" height="160" patternUnits="userSpaceOnUse">
<rect width="160" height="160" fill="#f4f4f4"/><line x1="0" y1="0" x2="160" y2="0" stroke="#c8c8c8" stroke-width="14"/></pattern></defs>""")
    o.append(f'<rect class="bg" width="{W}" height="{H}"/>')

    # двор и дворики
    o.append(rect_svg((4600, 25100, 200, 6600), "yard"))
    o.append(rect_svg((4600, 25100, 12400, 13900), "yard"))
    # полы помещений
    for _, rs, _, _ in ROOMS:
        for r in rs:
            o.append(rect_svg(r, "room"))
    for kind, r in EXTRA:
        o.append(rect_svg(r, "roof"))

    # сетка 1 м
    o.append('<g class="grid" id="grid">')
    for gx in range(0, 30001, 1000):
        o.append(f'<line x1="{sx(gx)}" y1="{sy(-200)}" x2="{sx(gx)}" y2="{sy(13800)}"/>')
    for gy in range(0, 14001, 1000):
        o.append(f'<line x1="{sx(-205)}" y1="{sy(gy)}" x2="{sx(29905)}" y2="{sy(gy)}"/>')
    o.append("</g>")

    # граница участка / соседи
    o.append(f'<polyline class="fence" points="{sx(-205)},{sy(14400)} {sx(29905)},{sy(14175)}"/>')
    o.append(f'<text class="small" x="{sx(9000)}" y="{sy(14550)}">граница участка / дом соседей</text>')

    # символы из PDF
    for kind, pts in syms:
        p = " ".join(f"{sx(x):.0f},{sy(y):.0f}" for x, y in pts)
        o.append(f'<polyline class="{kind}" points="{p}"/>')

    # стены
    for r in EXT:
        o.append(rect_svg(r, "ext"))
    for r in PART:
        o.append(rect_svg(r, "part"))
    for r in COL:
        o.append(rect_svg(r, "col"))
    # окна
    for x0, x1, y0, y1 in WIN:
        o.append(rect_svg((x0, x1, y0, y1), "win"))
        if (x1 - x0) >= (y1 - y0):
            ym = (y0 + y1) / 2
            o.append(f'<line class="winl" x1="{sx(x0)}" y1="{sy(ym)}" x2="{sx(x1)}" y2="{sy(ym)}"/>')
        else:
            xm = (x0 + x1) / 2
            o.append(f'<line class="winl" x1="{sx(xm)}" y1="{sy(y0)}" x2="{sx(xm)}" y2="{sy(y1)}"/>')

    # подписи ширины окон (снаружи помещения)
    for x0, x1, y0, y1 in WIN:
        if (x1 - x0) >= (y1 - y0) and x1 - x0 > 600:
            yy = y0 - 230 if y1 <= 300 or (6000 < y0 < 7100) else y1 + 250
            if 4000 < y0 < 4700:
                yy = y0 - 230
            if floor == 2 and 12000 <= y0 < 12500 and 10505 <= x0 <= 18700:
                yy = y0 - 250
            o.append(f'<text class="small" x="{sx((x0 + x1) / 2)}" y="{sy(yy)}" text-anchor="middle" fill="#2f8fd8">окно {cm(x1 - x0)}</text>')
        elif (y1 - y0) > 600 and (x1 - x0) >= 90:
            cx, cy = sx(x1 + 230), sy((y0 + y1) / 2)
            o.append(f'<text class="small" x="{cx}" y="{cy}" text-anchor="middle" fill="#2f8fd8" transform="rotate(-90 {cx} {cy})">окно {cm(y1 - y0)}</text>')

    # дверные проёмы
    for x, y, w, d in OPEN:
        if d == "h":
            o.append(f'<text class="small" x="{sx(x)}" y="{sy(y) + 65}" text-anchor="middle" fill="#8e44ad" font-weight="700">↕{cm(w)}</text>')
        else:
            o.append(f'<text class="small" x="{sx(x)}" y="{sy(y) + 65}" text-anchor="middle" fill="#8e44ad" font-weight="700">↔{cm(w)}</text>')

    # помещения: размеры и подписи
    for name, rs, dr, (lx, ly) in ROOMS:
        name, _, note = name.partition("|")
        sub = f"{area(rs):.1f} м²" if rs else ""
        if dr:
            x0, x1, y0, y1 = dr
            if min(x1 - x0, y1 - y0) >= 2500:
                o.append(dim_h(x0, x1, y0 + 330))
                o.append(dim_v(x0 + 330, y0, y1))
            else:
                sub = f"{cm(x1 - x0)}×{cm(y1 - y0)} · {sub}"
        o.append(f'<text class="name" x="{sx(lx)}" y="{sy(ly)}" text-anchor="middle">{name}</text>')
        dy = 300
        if note:
            o.append(f'<text class="small" x="{sx(lx)}" y="{sy(ly) + dy}" text-anchor="middle">{note}</text>')
            dy += 260
        if sub:
            o.append(f'<text class="sub" x="{sx(lx)}" y="{sy(ly) + dy}" text-anchor="middle">{sub}</text>')

    # общие габариты (по наружным граням)
    o.append(dim_h(-205, 29905, -1100, "3011 см (по наружным стенам)"))
    o.append(dim_v(-900, -200, 13800, "1400 см"))

    title = "1-й ЭТАЖ (отм. 0,000)" if floor == 1 else "2-й ЭТАЖ (отм. +3,300)"
    o.append(f'<text class="title" x="{sx(-205)}" y="{sy(16500)}">{title}</text>')
    o.append(f'<text class="note" x="{sx(-205)}" y="{sy(15800)}">Размеры в сантиметрах, «в чистоте» между стенами. '
             f'Красное — размеры помещений, синее — окна, фиолетовое — ширина проёмов. Сетка 1×1 м.</text>')
    o.append(f'<text class="note" x="{sx(29905)}" y="{sy(-2000)}" text-anchor="end">PDF на листе A3 — масштаб 1:100 (1 см на бумаге = 1 м)</text>')
    o.append(f'<text class="note" x="{sx(-205)}" y="{sy(-2000)}">Север не указан в чертеже. Внизу — общий двор, вверху — граница с соседями.</text>')
    o.append("</svg>")
    return "\n".join(o)


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    for f in (1, 2):
        with open(os.path.join(OUT, f"etazh-{f}.svg"), "w", encoding="utf-8") as fh:
            fh.write(build(f))
        print("ok", f)

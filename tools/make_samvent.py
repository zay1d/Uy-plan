"""Простой чертёж «СамВент» для мастеров: один лист A3, 1-й и 2-й этаж целиком.

Подписи — на левой половине дома, правая такая же (зеркально).
Запуск: python3 tools/make_samvent.py && node tools/render_samvent.js  ->  plan/samvent.pdf, plan/samvent.png
"""
import math
import os

import make_plan as mp
import samvent

S = 0.0086                    # мм бумаги на мм натуры (≈ 1:116)
XMIN, XMAX = -400, 30100
YMIN, YMAX = -700, 14500
PX0 = 12                      # левый край плана на листе, мм
FLOOR_Y0 = {2: 22, 1: 160}    # верх плана этажа на листе, мм

C = {"wall": "#2b2f33", "part": "#6f767c", "win": "#3d8fd1", "sup": "#1f74d1", "eta": "#e07b16",
     "eha": "#8a5a44", "door": "#2e9e55", "elec": "#6c3fc4", "flow": "#9aa3aa", "yard": "#eef4e8",
     "ink": "#1c2228", "muted": "#5b646b"}

V = samvent.data()
L_SIDE, R_SIDE = V["sides"]


class Plan:
    def __init__(self, floor):
        self.f = floor
        self.y0 = FLOOR_Y0[floor]

    def X(self, x):
        return PX0 + (x - XMIN) * S

    def Y(self, y):
        return self.y0 + (YMAX - y) * S


def rect(P, r, fill, stroke="none", sw=0):
    x0, x1, y0, y1 = r
    return (f'<rect x="{P.X(x0):.2f}" y="{P.Y(y1):.2f}" width="{(x1 - x0) * S:.2f}" height="{(y1 - y0) * S:.2f}" '
            f'fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>')


def txt(x, y, t, size=2.4, color=None, anchor="start", weight=400, halo=False):
    h = ' paint-order="stroke" stroke="#fff" stroke-width="0.9" stroke-linejoin="round"' if halo else ""
    return (f'<text x="{x:.2f}" y="{y:.2f}" font-size="{size}" fill="{color or C["ink"]}" text-anchor="{anchor}" '
            f'font-weight="{weight}"{h}>{t}</text>')


def poly(P, pts, color, w, dash=None, cap="round", marker=None):
    p = " ".join(f"{P.X(a[0]):.2f},{P.Y(a[1]):.2f}" for a in pts)
    d = f' stroke-dasharray="{dash}"' if dash else ""
    m = f' marker-end="url(#{marker})"' if marker else ""
    return (f'<polyline points="{p}" fill="none" stroke="{color}" stroke-width="{w}" stroke-linecap="{cap}" '
            f'stroke-linejoin="round"{d}{m}/>')


def defs():
    out = []
    for k in ("sup", "eha", "flow"):
        out.append(f'<marker id="a-{k}" viewBox="0 0 10 10" refX="7" refY="5" markerWidth="4.5" markerHeight="4.5" '
                   f'orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="{C[k]}"/></marker>')
    return "<defs>" + "".join(out) + "</defs>"


def fan_icon(cx, cy, r):
    blades = "".join(
        f'<path d="M{cx:.2f},{cy:.2f} q{r * 0.9 * math.cos(a + 0.6):.2f},{r * 0.9 * math.sin(a + 0.6):.2f} '
        f'{r * math.cos(a):.2f},{r * math.sin(a):.2f} z" fill="{C["ink"]}"/>' for a in (0, 2.094, 4.189))
    return f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="{r:.2f}" fill="#fff" stroke="{C["ink"]}" stroke-width="0.35"/>' + blades


def valve_sym(x, y, nx, ny, r=1.55):
    return (f'<line x1="{x:.2f}" y1="{y:.2f}" x2="{x + nx * 5.5:.2f}" y2="{y - ny * 5.5:.2f}" stroke="{C["sup"]}" '
            f'stroke-width="0.7" marker-end="url(#a-sup)"/>'
            f'<circle cx="{x:.2f}" cy="{y:.2f}" r="{r}" fill="{C["sup"]}" stroke="#fff" stroke-width="0.3"/>'
            + txt(x, y + 0.75, "К", 2.0, "#fff", "middle", 700))


def grille_sym(x, y, a=1.9):
    return (f'<rect x="{x - a:.2f}" y="{y - a:.2f}" width="{2 * a}" height="{2 * a}" fill="#fff" stroke="{C["eta"]}" stroke-width="0.55"/>'
            f'<path d="M{x - a:.2f},{y - a:.2f} l{2 * a},{2 * a} M{x + a:.2f},{y - a:.2f} l-{2 * a},{2 * a}" stroke="{C["eta"]}" stroke-width="0.45"/>')


def elec_sym(x, y, n, r=1.7):
    return (f'<circle cx="{x:.2f}" cy="{y:.2f}" r="{r}" fill="#fff" stroke="{C["elec"]}" stroke-width="0.55"/>'
            + txt(x, y + 0.75, str(n), 2.1, C["elec"], "middle", 700))


ROOM_NAMES = {
    2: {"Комната (родители)": "Родители", "Детская": "Детская", "С/у": "С/у", "Кладовая": "Кладовая",
        "Холл": "Холл", "С/у общий": "С/у общий"},
    1: {"Крыло": "Гостиная", "Комната": "Комната", "Холл": "Холл",
        "Тамбур (витраж)": "Тамбур"},
}
BIG = {"Родители", "Детская", "Гостиная", "Комната"}


def floor_svg(floor):
    P = Plan(floor)
    samvent.wall_rects(floor)
    o = []
    # дворы
    o.append(rect(P, [4600, 25100, 200, 6600], C["yard"]))
    o.append(rect(P, [4600, 25100, 12400, 14100], C["yard"]))
    o.append(txt(P.X(14850), P.Y(3600), "ДВОР", 3.2, "#9db48f", "middle", 700))
    if floor == 1:
        o.append(txt(P.X(14850), P.Y(13450), "ЗАДНИЙ ДВОР", 2.6, "#9db48f", "middle", 700))
    for name, rects, dim, lab in mp.ROOMS:
        for r in rects:
            o.append(rect(P, r, "#fbfaf6"))
    for r in mp.EXTRA:
        o.append(rect(P, r[1], "#ececec"))
    # лестницы — штриховка ступеней
    for x0, x1 in ((4600, 8495), (21195, 25100)):
        o.append(rect(P, [x0, x1, 8150, 12000], "#f1f0ec", "#cfccc5", 0.2))
        for k in range(9):
            yy = 8150 + (k + 1) * 380
            o.append(f'<line x1="{P.X(x0 + 50):.2f}" y1="{P.Y(yy):.2f}" x2="{P.X(x0 + 650):.2f}" y2="{P.Y(yy):.2f}" stroke="#d6d3cc" stroke-width="0.2"/>')
            o.append(f'<line x1="{P.X(x1 - 650):.2f}" y1="{P.Y(yy):.2f}" x2="{P.X(x1 - 50):.2f}" y2="{P.Y(yy):.2f}" stroke="#d6d3cc" stroke-width="0.2"/>')
    for r in mp.EXT + mp.COL:
        o.append(rect(P, r, C["wall"]))
    for r in mp.PART:
        o.append(rect(P, r, C["part"]))
    for r in mp.WIN:
        o.append(rect(P, r, "#fff", C["win"], 0.28))
    # подписи комнат
    names = ROOM_NAMES[floor]
    for name, rects, dim, (lx, ly) in mp.ROOMS:
        n = name.partition("|")[0]
        if n not in names:
            continue
        lab = names[n]
        big = lab in BIG
        dy = 0
        if floor == 2:
            dy = {"С/у": -350, "Кладовая": 330, "Холл": -300, "С/у общий": -550}.get(lab, 0)
        if floor == 1:
            dy = {"Ванная": -350, "С/у": 300, "Тамбур": 0, "Гостиная": -1200}.get(lab, 0)
        dx = 0
        if lab == "С/у" and floor == 2:
            dx = 500 if lx < 14850 else -500
        if lab == "Холл":
            dx = -1100 if lx < 14850 else 1100
        o.append(txt(P.X(lx + dx), P.Y(ly + dy), lab, 3.1 if big else 2.2, C["ink"] if big else C["muted"],
                     "middle", 700 if big else 600, halo=True))

    for side in (L_SIDE, R_SIDE):
        for f in side["flows"]:
            if f["floor"] == floor:
                o.append(poly(P, f["pts"], C["flow"], 0.45, dash="1.2 0.9", marker="a-flow"))
        for d in side["ducts"]:
            if d["floor"] == floor and d["zone"] == "flex":
                o.append(poly(P, d["pts"], C["eta"], 0.72))
        for ol in side["outlets"]:
            if ol["floor"] == floor:
                a, b = ol["pts"]
                o.append(poly(P, [a, [b[0], b[1] - 120]], C["eha"], 1.8, cap="butt", marker="a-eha"))
        for u in side["units"]:
            if u["floor"] == floor:
                r = u["rect"]
                o.append(rect(P, r, "#fff", C["ink"], 0.4))
                o.append(fan_icon(P.X((r[0] + r[1]) / 2), P.Y((r[2] + r[3]) / 2), 1.9))
        for g in side["grilles"]:
            if g["floor"] != floor:
                continue
            x, y = P.X(g["pos"][0]), P.Y(g["pos"][1])
            if g["type"] == "eta":
                o.append(grille_sym(x, y))
        for g in side["grilles"]:
            if g["floor"] == floor and g["type"] == "sup":
                o.append(valve_sym(P.X(g["pos"][0]), P.Y(g["pos"][1]), *g["n"]))
        for dd in side["doors"]:
            if dd["floor"] != floor:
                continue
            x, y = P.X(dd["pos"][0]), P.Y(dd["pos"][1])
            if dd["dir"] == "h":
                o.append(f'<line x1="{x - 2.2:.2f}" y1="{y:.2f}" x2="{x + 2.2:.2f}" y2="{y:.2f}" stroke="{C["door"]}" stroke-width="0.9"/>')
            else:
                o.append(f'<line x1="{x:.2f}" y1="{y - 2.2:.2f}" x2="{x:.2f}" y2="{y + 2.2:.2f}" stroke="{C["door"]}" stroke-width="0.9"/>')
        for w in side["wires"]:
            if w["floor"] == floor:
                o.append(poly(P, w["pts"], C["elec"], 0.4, dash="1 0.7"))
        for e in side["elec"]:
            if e["floor"] != floor:
                continue
            x, y = P.X(e["pos"][0]), P.Y(e["pos"][1])
            if e.get("nrm"):
                y -= e["nrm"][1] * 3.4
            if e["kind"] == "fan_power":
                u = next(u for u in side["units"] if u["floor"] == floor)
                r = u["rect"]
                left = side["side"] == "L"
                x, y = P.X(r[0] if left else r[1]) + (-2.6 if left else 2.6), P.Y((r[2] + r[3]) / 2)
            o.append(elec_sym(x, y, e["n"]))
    o += labels(P, floor)
    return "\n".join(o)


def labels(P, f):
    """Подписи только на левой половине (правая такая же)."""
    L = []
    t = lambda x, y, s, col, anc="start", dx=0, dy=0, size=2.0: L.append(
        txt(P.X(x) + dx, P.Y(y) + dy, s, size, C[col], anc, 700, True))
    if f == 2:
        t(2200, 900, "К·К: h 2,1 м, 50 см от углов", "sup", "middle")
        t(3950, 12250, "К·К над окном, h 2,65", "sup", "end")
        t(13700, 7550, "К: h 2,1 м", "sup", "end")
        t(13700, 11300, "К: h 2,1 м", "sup", "end")
        t(1540, 5900, "В1·120", "eta", dx=2.6, dy=-0.8)
        t(2200, 7900, "В2·90", "eta", dx=2.6, dy=0.8)
        t(9950, 10800, "В3·120", "eta", "end", dx=-2.6, dy=0.8)
        t(5150, 9900, "5 труб Ø90", "eta")
        t(9300, 11650, "3 трубы", "eta", "middle", dy=-2.2)
        t(7800, 11450, "вентилятор 1", "ink", "middle", dy=3.0)
        t(7800, 12650, "выброс во двор", "eha", dx=2, dy=-0.4)
        t(7300, 7000, "регулятор", "elec", "middle", dy=-6.2)
    else:
        t(2200, 900, "К·К: h 2,1 м, 50 см от углов", "sup", "middle")
        t(3950, 12350, "К над окном, h 2,65", "sup", "end")
        t(13700, 7550, "К: h 2,1 м", "sup", "end")
        t(13700, 11300, "К: h 2,1 м", "sup", "end")
        t(9300, 10600, "В4 ванная·160", "eta", "end", dx=-2.6, dy=0.8)
        t(10000, 9560, "В5 с/у·120", "eta", "start", dx=2.6, dy=0.8)
        t(9050, 11575, "вентилятор 2", "ink", "end", dx=-5.2, dy=0.8)
        t(10250, 12650, "выброс во двор", "eha", dx=2, dy=-0.4)
        t(9000, 8800, "регулятор", "elec", "middle", dy=6.5)
    return L


def floor_title(f):
    P = Plan(f)
    title = "2-й ЭТАЖ — спальни" if f == 2 else "1-й ЭТАЖ — гостиная и комната"
    return (txt(PX0, P.y0 - 4.5, title, 4.2, C["ink"], weight=700)
            + txt(PX0 + (86 if f == 2 else 106), P.y0 - 4.5, "подписи слева — правая половина такая же", 2.6, C["muted"]))


def panel_svg():
    x = 288
    o = []
    y = 20
    o.append(txt(x, y, "Вентиляция «СамВент»", 6.4, C["ink"], weight=700)); y += 5.8
    o.append(txt(x, y, "весь дом · 1-й и 2-й этаж", 3.4, C["muted"], weight=600)); y += 8.5

    def h(s):
        nonlocal y
        o.append(txt(x, y, s, 2.7, C["muted"], weight=700)); y += 4.6

    def line(s, color=None, size=2.85, dy=4.1, weight=400):
        nonlocal y
        o.append(txt(x, y, s, size, color, weight=weight)); y += dy

    h("КАК РАБОТАЕТ")
    line("1. Воздух с улицы входит в комнаты через клапаны К.")
    line("2. Проходит под дверью (щель 2 см) в коридор.")
    line("3. Вентилятор тянет его из санузлов и кладовой")
    line("    (решётки В) по трубам и выбрасывает во двор.")
    y += 3.5

    h("ОБОЗНАЧЕНИЯ")
    for mk, label in [
        (lambda yy: valve_sym(x + 2, yy - 1, 0, 0), "клапан в стене (без электричества)"),
        (lambda yy: grille_sym(x + 2, yy - 1), "вытяжная решётка в потолке, h 2,45 м"),
        (lambda yy: f'<line x1="{x}" y1="{yy - 1}" x2="{x + 4.5}" y2="{yy - 1}" stroke="{C["eta"]}" stroke-width="0.8"/>',
         "гибкая труба Ø90 (1 линия = 1 труба)"),
        (lambda yy: fan_icon(x + 2, yy - 1, 1.9), "вентилятор + коллектор (под потолком)"),
        (lambda yy: f'<line x1="{x}" y1="{yy - 1}" x2="{x + 4.5}" y2="{yy - 1}" stroke="{C["eha"]}" stroke-width="1.8"/>',
         "выброс Ø160 через стену во двор"),
        (lambda yy: f'<line x1="{x + 0.6}" y1="{yy - 1}" x2="{x + 3.8}" y2="{yy - 1}" stroke="{C["door"]}" stroke-width="1"/>',
         "щель 2 см под дверью"),
        (lambda yy: elec_sym(x + 2, yy - 1, 1), "электрика (см. ниже)"),
    ]:
        o.append(mk(y) + txt(x + 6.5, y, label, 2.85))
        y += 4.9
    y += 2.5

    h("СКОЛЬКО ВОЗДУХА (одна половина дома)")
    rows = [("2 эт.", "Родители", "2 К", "120", "В1 с/у · 3 трубы"),
            ("", "Детская (крыло)", "2 К", "90", "В2 кладовая · 2 трубы"),
            ("", "Детская (центр)", "2 К", "120", "В3 общий с/у · 3 трубы"),
            ("1 эт.", "Гостиная (крыло)", "3 К", "160", "В4 ванная · 4 трубы"),
            ("", "Комната (центр)", "2 К", "120", "В5 с/у · 3 трубы")]
    for fl, a, b, c, d in rows:
        if fl == "1 эт.":
            o.append(f'<line x1="{x}" y1="{y - 3}" x2="{x + 118}" y2="{y - 3}" stroke="#dde" stroke-width="0.25"/>')
        o.append(txt(x, y, fl, 2.6, C["muted"], weight=700) + txt(x + 9, y, a, 2.8, weight=600)
                 + txt(x + 39.5, y, b, 2.8, C["sup"]) + txt(x + 53, y, c, 2.8, weight=700, anchor="end")
                 + txt(x + 55, y, d, 2.7, C["eta"]))
        y += 4.2
    o.append(f'<line x1="{x}" y1="{y - 2.8}" x2="{x + 118}" y2="{y - 2.8}" stroke="#bbc" stroke-width="0.3"/>')
    o.append(txt(x, y + 0.5, "Вентилятор 1 (2 эт.): 330 м³/ч → брать 350–400", 2.8, weight=700)); y += 4.2
    o.append(txt(x, y + 0.5, "Вентилятор 2 (1 эт.): 280 м³/ч → брать 300–350", 2.8, weight=700)); y += 8

    h("ПОЧЕМУ ПО 3 ТРУБЫ")
    line("Одна гибкая труба Ø90 тихо пропускает ~40–45 м³/ч.")
    line("Если гнать больше — шумит. Поэтому: 120 м³/ч = 3 трубы,")
    line("90 = 2 трубы, 160 = 4 трубы. Каждую трубу на коллекторе")
    line("можно подкрутить дросселем отдельно.")
    y += 3.5

    h("ЭЛЕКТРИКА (одна половина дома)")
    line("① вентилятор 1 — коробка у вентилятора, 2-й эт.", C["elec"])
    line("② регулятор 1 — холл 2-го эт., h 1,5 м", C["elec"])
    line("③ вентилятор 2 — коробка в потолке ванной, 1-й эт.", C["elec"])
    line("④ регулятор 2 — холл 1-го эт., у двери с/у, h 1,5 м", C["elec"])
    line("Кабель 3×1,5 от щита (автомат 10 А): щит → ② → ①,")
    line("и отдельно щит → ④ → ③.")
    y += 3.5

    n_pipe = samvent.pipe_length(V)
    h("КУПИТЬ (на весь дом)")
    line("• 22 стеновых клапана Ø125 с фильтром")
    line("• 4 тихих канальных вентилятора: 2 × 350–400 и 2 × 300–350")
    line("• 4 коллектора на 8 труб с дросселями + 4 глушителя")
    line(f"• ~{n_pipe} м гибкой трубы Ø90 · 10 потолочных решёток")
    line("• 4 фасадные решётки Ø160 с обратным клапаном")
    y += 3.5

    h("ВАЖНО")
    line("• Окна плотные, иначе воздух пойдёт через окна.")
    line("• Потолок комнат не трогаем; короб ~50×10 см под трубы —")
    line("  только в холле, коридоре и над лестницей.")
    line("• Кухонная вытяжка — отдельно, в эту систему не входит.")
    line("• Кровлю не сверлим: выброс через заднюю стену.")
    return "\n".join(o)


def page():
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 420 297" width="420mm" height="297mm"
 font-family="DejaVu Sans, Arial, sans-serif">
<rect width="420" height="297" fill="#fff"/>
{defs()}
<rect x="6" y="6" width="408" height="285" fill="none" stroke="#c8cdd2" stroke-width="0.4"/>
<line x1="283" y1="12" x2="283" y2="285" stroke="#dde1e4" stroke-width="0.4"/>
<line x1="12" y1="148.5" x2="277" y2="148.5" stroke="#dde1e4" stroke-width="0.4"/>
{floor_title(2)}
{floor_svg(2)}
{floor_title(1)}
{floor_svg(1)}
{panel_svg()}
</svg>"""


if __name__ == "__main__":
    os.makedirs(mp.OUT, exist_ok=True)
    with open(os.path.join(mp.OUT, "samvent.svg"), "w", encoding="utf-8") as fh:
        fh.write(page())
    print("ok plan/samvent.svg")

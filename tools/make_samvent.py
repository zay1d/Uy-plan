"""Простой чертёж «СамВент» для мастеров: один лист A3, левая половина 2-го этажа крупно.

Запуск: python3 tools/make_samvent.py && node tools/render_samvent.js  ->  plan/samvent.pdf, plan/samvent.png
"""
import math
import os

import make_plan as mp
import samvent

S = 0.018                      # мм бумаги на мм натуры (≈ 1:55)
X0, Y0 = 12, 20                # левый верхний угол плана на листе, мм
XMIN, YMAX = -700, 14600
XCUT = 14650                   # левая половина дома (до середины центральной стены)

C = {"wall": "#2b2f33", "part": "#6f767c", "win": "#3d8fd1", "sup": "#1f74d1", "eta": "#e07b16",
     "eha": "#8a5a44", "door": "#2e9e55", "elec": "#6c3fc4", "flow": "#9aa3aa", "yard": "#eef4e8",
     "ink": "#1c2228", "muted": "#5b646b"}


def X(x):
    return X0 + (x - XMIN) * S


def Y(y):
    return Y0 + (YMAX - y) * S


def rect(r, fill, stroke="none", sw=0, extra=""):
    x0, x1, y0, y1 = r
    x0, x1 = max(x0, XMIN), min(x1, XCUT)
    if x1 <= x0:
        return ""
    return (f'<rect x="{X(x0):.2f}" y="{Y(y1):.2f}" width="{(x1 - x0) * S:.2f}" height="{(y1 - y0) * S:.2f}" '
            f'fill="{fill}" stroke="{stroke}" stroke-width="{sw}" {extra}/>')


def txt(x, y, t, size=3.0, color=None, anchor="start", weight=400, halo=False):
    h = ' paint-order="stroke" stroke="#fff" stroke-width="1.1" stroke-linejoin="round"' if halo else ""
    return (f'<text x="{x:.2f}" y="{y:.2f}" font-size="{size}" fill="{color or C["ink"]}" text-anchor="{anchor}" '
            f'font-weight="{weight}"{h}>{t}</text>')


def poly(pts, color, w, dash=None, cap="round", marker=None, op=1):
    p = " ".join(f"{X(a[0]):.2f},{Y(a[1]):.2f}" for a in pts)
    d = f' stroke-dasharray="{dash}"' if dash else ""
    m = f' marker-end="url(#{marker})"' if marker else ""
    return (f'<polyline points="{p}" fill="none" stroke="{color}" stroke-width="{w}" stroke-linecap="{cap}" '
            f'stroke-linejoin="round" opacity="{op}"{d}{m}/>')


def defs():
    out = []
    for k in ("sup", "eta", "eha", "flow"):
        out.append(f'<marker id="a-{k}" viewBox="0 0 10 10" refX="7" refY="5" markerWidth="5" markerHeight="5" '
                   f'orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="{C[k]}"/></marker>')
    return "<defs>" + "".join(out) + "</defs>"


def fan_icon(cx, cy, r):
    blades = "".join(
        f'<path d="M{cx:.2f},{cy:.2f} q{r * 0.9 * math.cos(a + 0.6):.2f},{r * 0.9 * math.sin(a + 0.6):.2f} '
        f'{r * math.cos(a):.2f},{r * math.sin(a):.2f} z" fill="{C["ink"]}"/>' for a in (0, 2.094, 4.189))
    return f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="{r:.2f}" fill="#fff" stroke="{C["ink"]}" stroke-width="0.4"/>' + blades


def plan_svg():
    side = samvent.data()["sides"][0]
    samvent.wall_rects()                      # заполняет mp.* геометрией 2-го этажа
    o = [defs()]
    # дворы
    o.append(rect([4600, 14650, 200, 6600], C["yard"]))
    o.append(rect([4600, 14650, 12400, 14300], C["yard"]))
    o.append(txt(X(9600), Y(3400), "ДВОР", 4, "#8fa883", "middle", 700))
    o.append(txt(X(7000), Y(13650), "ЗАДНИЙ ДВОР", 3.2, "#8fa883", "middle", 700))
    # полы комнат
    for name, rects, dim, lab in mp.ROOMS:
        for r in rects:
            o.append(rect(r, "#fbfaf6"))
    # лестница — контур
    o.append(rect([4600, 8495, 8150, 12000], "#f1f0ec", "#c9c6bf", 0.25))
    for k in range(9):
        yy = 8150 + (k + 1) * 380
        o.append(f'<line x1="{X(4650):.2f}" y1="{Y(yy):.2f}" x2="{X(5300):.2f}" y2="{Y(yy):.2f}" stroke="#d3d0c9" stroke-width="0.25"/>')
        o.append(f'<line x1="{X(7850):.2f}" y1="{Y(yy):.2f}" x2="{X(8450):.2f}" y2="{Y(yy):.2f}" stroke="#d3d0c9" stroke-width="0.25"/>')
    # стены, окна
    for r in mp.EXT + mp.COL:
        o.append(rect(r, C["wall"]))
    for r in mp.PART:
        o.append(rect(r, C["part"]))
    for r in mp.WIN:
        o.append(rect(r, "#fff", C["win"], 0.35))
    # подписи комнат
    names = {"Комната (родители)": "Родители", "Детская": "Детская", "С/у": "С/у", "Кладовая": "Кладовая",
             "Холл": "Холл", "С/у общий": "С/у общий"}
    seen = set()
    for name, rects, dim, (lx, ly) in mp.ROOMS:
        n = name.partition("|")[0]
        if lx > XCUT or n not in names or (n, lx) in seen:
            continue
        seen.add((n, lx))
        big = n in ("Комната (родители)", "Детская")
        dy = {"С/у": 0, "Кладовая": 450, "Лестница": -700, "С/у общий": -500, "Холл": -300}.get(n, 0)
        dx = {"Холл": -900, "С/у": 900, "Кладовая": -350}.get(n, 0)
        if n == "С/у":
            dy, dx = 300, 1100
        o.append(txt(X(lx + dx), Y(ly + dy), names[n], 4.6 if big else 3.2, C["ink"] if big else C["muted"],
                     "middle", 700 if big else 600, halo=True))
    # путь воздуха
    for f in side["flows"]:
        o.append(poly(f, C["flow"], 0.6, dash="1.6 1.2", marker="a-flow"))
    # трубы вытяжки (каждая труба Ø90)
    for d in side["ducts"]:
        if d["zone"] == "flex":
            o.append(poly(d["pts"], C["eta"], 1.25))
    # выброс во двор
    out = side["outlet"]
    o.append(poly([out[0], [out[1][0], out[1][1] - 150]], C["eha"], 2.6, cap="butt", marker="a-eha"))
    # вентилятор + коллектор
    fr = side["unit"]["rect"]
    o.append(rect(fr, "#fff", C["ink"], 0.5))
    o.append(fan_icon(X((fr[0] + fr[1]) / 2), Y((fr[2] + fr[3]) / 2), 3.1))
    # решётки вытяжки
    for g in side["grilles"]:
        x, y = X(g["pos"][0]), Y(g["pos"][1])
        if g["type"] == "eta":
            o.append(f'<rect x="{x - 2.6:.2f}" y="{y - 2.6:.2f}" width="5.2" height="5.2" fill="#fff" stroke="{C["eta"]}" stroke-width="0.7"/>'
                     f'<path d="M{x - 2.6:.2f},{y - 2.6:.2f} l5.2,5.2 M{x + 2.6:.2f},{y - 2.6:.2f} l-5.2,5.2" stroke="{C["eta"]}" stroke-width="0.6"/>')
    # клапаны притока
    for g in side["grilles"]:
        if g["type"] != "sup":
            continue
        x, y = X(g["pos"][0]), Y(g["pos"][1])
        nx, ny = g["n"]
        o.append(f'<line x1="{x:.2f}" y1="{y:.2f}" x2="{x + nx * 8:.2f}" y2="{y - ny * 8:.2f}" stroke="{C["sup"]}" '
                 f'stroke-width="0.9" marker-end="url(#a-sup)"/>')
        o.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="2.3" fill="{C["sup"]}" stroke="#fff" stroke-width="0.4"/>'
                 + txt(x, y + 1.05, "К", 2.8, "#fff", "middle", 700))
    # щели под дверями
    for dd in side["doors"]:
        x, y = X(dd["pos"][0]), Y(dd["pos"][1])
        if dd["dir"] == "h":
            o.append(f'<line x1="{x - 3:.2f}" y1="{y:.2f}" x2="{x + 3:.2f}" y2="{y:.2f}" stroke="{C["door"]}" stroke-width="1.2"/>')
        else:
            o.append(f'<line x1="{x:.2f}" y1="{y - 3:.2f}" x2="{x:.2f}" y2="{y + 3:.2f}" stroke="{C["door"]}" stroke-width="1.2"/>')
    # электрика
    for w in side["wires"]:
        o.append(poly(w["pts"], C["elec"], 0.5, dash="1.2 0.9"))
    for e in side["elec"]:
        x, y = X(e["pos"][0]), Y(e["pos"][1])
        if e.get("nrm"):
            y -= e["nrm"][1] * 4.5
        if e["kind"] == "fan_power":
            x, y = X(fr[0]) - 3.5, Y((fr[2] + fr[3]) / 2)
        o.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="2.4" fill="#fff" stroke="{C["elec"]}" stroke-width="0.7"/>'
                 + txt(x, y + 1.05, str(e["n"]), 2.9, C["elec"], "middle", 700))

    # --- подписи (вручную, чтобы ничего не налезало)
    L = []
    L.append(txt(X(2200), Y(1050), "2 клапана: h 2,1 м, по 50 см от углов", 2.6, C["sup"], "middle", 700, True))
    L.append(txt(X(3700), Y(12900) + 1, "2 клапана над окном, h 2,65 м", 2.6, C["sup"], "end", 700, True))
    L.append(txt(X(13800), Y(7550), "К: h 2,1 м, 40 см от угла", 2.6, C["sup"], "end", 700, True))
    L.append(txt(X(13800), Y(11100), "К: h 2,1 м, 40 см от угла", 2.6, C["sup"], "end", 700, True))
    ex = {e["id"]: e for e in side["exhausts"]}
    L.append(txt(X(1540) + 4, Y(5900) - 1.5, "В1 · 120 м³/ч", 2.8, C["eta"], "start", 700, True))
    L.append(txt(X(2200) + 4, Y(7900) + 1, "В2 · 90", 2.8, C["eta"], "start", 700, True))
    L.append(txt(X(9950) - 4, Y(10800) + 1, "В3 · 120 м³/ч", 2.8, C["eta"], "end", 700, True))
    L.append(txt(X(5400), Y(9800), "5 труб Ø90", 2.6, C["eta"], "start", 700, True))
    L.append(txt(X(5400), Y(9800) + 3.4, "под потолком", 2.6, C["eta"], "start", 700, True))
    L.append(txt(X(9200), Y(11700) - 3.5, "3 трубы Ø90", 2.6, C["eta"], "middle", 700, True))
    L.append(txt(X(7800), Y(11450) + 4.2, "вентилятор + коллектор", 2.6, C["ink"], "middle", 700, True))
    L.append(txt(X(7800) + 3, Y(12650) - 1, "выброс во двор, h 2,9 м", 2.6, C["eha"], "start", 700, True))
    L.append(txt(X(3650), Y(4915) + 4.2, "щель 2 см", 2.2, C["door"], "middle", 600, True))
    L.append(txt(X(3650), Y(8460) - 2.4, "щель 2 см", 2.2, C["door"], "middle", 600, True))
    L.append(txt(X(11275) - 2.5, Y(7700) + 1, "щель 2 см", 2.2, C["door"], "end", 600, True))
    L.append(txt(X(9950), Y(9240) + 4.2, "щель 2 см", 2.2, C["door"], "middle", 600, True))
    L.append(txt(X(7300), Y(7000) - 8.5, "регулятор h 1,5 м", 2.4, C["elec"], "middle", 700, True))
    o += L
    # контур листа плана: подпись оси Г
    return "\n".join(o)


def panel_svg():
    side = samvent.data()["sides"][0]
    x = 302
    o = []
    y = 26
    o.append(txt(x, y, "Вентиляция «СамВент»", 7.2, C["ink"], weight=700)); y += 7
    o.append(txt(x, y, "2-й этаж · левая половина дома", 4, C["muted"], weight=600)); y += 5.2
    o.append(txt(x, y, "Правая половина — зеркально, всё так же.", 3.3, C["muted"])); y += 10

    o.append(txt(x, y, "КАК РАБОТАЕТ", 3, C["muted"], weight=700)); y += 5.5
    for t in ("1. Свежий воздух входит в спальни через", "    клапаны К в наружных стенах.",
              "2. Идёт под дверью (щель 2 см) в коридор.",
              "3. Вентилятор вытягивает воздух из санузлов",
              "    и кладовой (В1–В3) и выбрасывает во двор."):
        o.append(txt(x, y, t, 3.3)); y += 4.6
    y += 5

    o.append(txt(x, y, "ОБОЗНАЧЕНИЯ", 3, C["muted"], weight=700)); y += 5.5
    o.append(f'<circle cx="{x + 2.5}" cy="{y - 1.1}" r="2.3" fill="{C["sup"]}"/>' + txt(x + 2.5, y, "К", 2.8, "#fff", "middle", 700)
             + txt(x + 8, y, "приточный клапан в стене (без электричества)", 3.1)); y += 6
    o.append(f'<rect x="{x}" y="{y - 3.7}" width="5" height="5" fill="#fff" stroke="{C["eta"]}" stroke-width="0.7"/>'
             f'<path d="M{x},{y - 3.7} l5,5 M{x + 5},{y - 3.7} l-5,5" stroke="{C["eta"]}" stroke-width="0.6"/>'
             + txt(x + 8, y, "вытяжная решётка в потолке (2,45 м)", 3.1)); y += 6
    o.append(f'<line x1="{x}" y1="{y - 1.2}" x2="{x + 5.5}" y2="{y - 1.2}" stroke="{C["eta"]}" stroke-width="1.25"/>'
             + txt(x + 8, y, "гибкая труба Ø90 (каждая линия — 1 труба)", 3.1)); y += 6
    o.append(fan_icon(x + 2.6, y - 1.2, 2.5) + txt(x + 8, y, "вентилятор 350–400 м³/ч + коллектор", 3.1)); y += 6
    o.append(f'<line x1="{x}" y1="{y - 1.2}" x2="{x + 5.5}" y2="{y - 1.2}" stroke="{C["eha"]}" stroke-width="2.4"/>'
             + txt(x + 8, y, "выброс Ø160 во двор (решётка с клапаном)", 3.1)); y += 6
    o.append(f'<line x1="{x + 1}" y1="{y - 1.2}" x2="{x + 4.5}" y2="{y - 1.2}" stroke="{C["door"]}" stroke-width="1.3"/>'
             + txt(x + 8, y, "щель под дверью 2 см (или переточная решётка)", 3.1)); y += 6
    o.append(f'<line x1="{x}" y1="{y - 1.2}" x2="{x + 5.5}" y2="{y - 1.2}" stroke="{C["flow"]}" stroke-width="0.6" stroke-dasharray="1.6 1.2"/>'
             + txt(x + 8, y, "путь воздуха", 3.1)); y += 6
    o.append(f'<circle cx="{x + 2.5}" cy="{y - 1.1}" r="2.3" fill="#fff" stroke="{C["elec"]}" stroke-width="0.7"/>'
             + txt(x + 2.5, y, "1", 2.8, C["elec"], "middle", 700) + txt(x + 8, y, "электрика (ниже)", 3.1)); y += 10

    o.append(txt(x, y, "СКОЛЬКО ВОЗДУХА (одна половина)", 3, C["muted"], weight=700)); y += 5.5
    rows = [("Родители", "2 клапана", "120", "В1 с/у · 3 трубы"),
            ("Детская (крыло)", "2 клапана", "90", "В2 кладовая · 2 трубы"),
            ("Детская (центр)", "2 клапана", "120", "В3 общий с/у · 3 трубы")]
    for a, b, c, d in rows:
        o.append(txt(x, y, a, 3.1, weight=600) + txt(x + 31, y, b, 3.1, C["sup"]) + txt(x + 58, y, c, 3.1, weight=700, anchor="end")
                 + txt(x + 61, y, d, 3.0, C["eta"])); y += 4.8
    o.append(f'<line x1="{x}" y1="{y - 3}" x2="{x + 108}" y2="{y - 3}" stroke="#ccd" stroke-width="0.3"/>')
    o.append(txt(x, y + 0.6, "Итого", 3.1, weight=700) + txt(x + 58, y + 0.6, "330 м³/ч", 3.1, weight=700, anchor="end")
             + txt(x + 61, y + 0.6, "→ вентилятор 350–400", 3.0, weight=700)); y += 11

    o.append(txt(x, y, "ЭЛЕКТРИКА (одна половина)", 3, C["muted"], weight=700)); y += 5.5
    for t in ("① Вентилятор — коробка под потолком лестницы.",
              "② Регулятор скорости — холл, h 1,5 м.",
              "Кабель 3×1,5 от щита (автомат 10 А) → ② → ①."):
        o.append(txt(x, y, t, 3.1, C["elec"] if t[0] in "①②" else C["ink"])); y += 4.8
    y += 5

    o.append(txt(x, y, "КУПИТЬ (на весь дом)", 3, C["muted"], weight=700)); y += 5.5
    for t in ("• 12 стеновых клапанов Ø125 с фильтром",
              "• 2 тихих канальных вентилятора 350–400 м³/ч",
              "• 2 коллектора на 8 труб, с дросселями",
              "• ~150 м гибкой трубы Ø90 (антибактериальной)",
              "• 6 потолочных решёток (на 2–3 трубы)",
              "• 2 глушителя + 2 фасадные решётки с клапаном"):
        o.append(txt(x, y, t, 3.1)); y += 4.6
    y += 5

    o.append(txt(x, y, "ВАЖНО", 3, C["muted"], weight=700)); y += 5.5
    for t in ("• Окна плотные (пластик), иначе воздух пойдёт",
              "   через окна, а не через клапаны.",
              "• Потолок спален не трогаем. В холле, коридоре",
              "   и лестнице — короб ~50×10 см под трубы.",
              "• Кровлю не сверлим: выброс через заднюю стену."):
        o.append(txt(x, y, t, 3.1)); y += 4.6
    return "\n".join(o)


def page():
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 420 297" width="420mm" height="297mm"
 font-family="DejaVu Sans, Arial, sans-serif">
<rect width="420" height="297" fill="#fff"/>
<rect x="6" y="6" width="408" height="285" fill="none" stroke="#c8cdd2" stroke-width="0.4"/>
<line x1="297" y1="12" x2="297" y2="285" stroke="#dde1e4" stroke-width="0.4"/>
{plan_svg()}
{panel_svg()}
</svg>"""


if __name__ == "__main__":
    os.makedirs(mp.OUT, exist_ok=True)
    with open(os.path.join(mp.OUT, "samvent.svg"), "w", encoding="utf-8") as fh:
        fh.write(page())
    print("ok plan/samvent.svg")

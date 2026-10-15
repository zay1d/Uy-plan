"""Чертежи вентиляции спален (для строителей и электрика).

plan/vent-1-etazh-2.svg  — 2-й этаж: шахты, трубы в подшивных потолках, решётки с привязками
plan/vent-2-krovlya.svg  — кровля: рекуператоры, утеплённые трубы, забор и выброс
plan/vent-3-etazh-1.svg  — 1-й этаж: резерв под комнату
plan/vent-4-spec.html    — разрез и спецификация (трубы, решётки, кабели)

Запуск: python3 tools/make_vent.py && node tools/render_vent.js
"""
import os
import re

import make_plan as mp
import vent

COL = {"sup": "#2f7fd6", "eta": "#de8a2c", "oda": "#3f9e4d", "eha": "#8a5a44"}
NAME = {"sup": "П", "eta": "В"}
PURPLE = "#6c4fb3"
V = vent.data()
mp.VB = (-2600, -2600, 32700, 17200)   # шире поле слева/справа под выноски шахт
L, R = V["sides"]


def base(floor, title, notes, pre=""):
    svg = mp.build(floor)
    svg = re.sub(r'<text class="title"[^>]*>.*?</text>', "", svg)
    svg = re.sub(r'<text class="note"[^>]*>.*?</text>\n?', "", svg)
    head = (f'<text class="title" x="{mp.sx(-205)}" y="{mp.sy(16500)}">{title}</text>'
            + "".join(f'<text class="note" x="{mp.sx(-205)}" y="{mp.sy(15800 - i * 330)}">{t}</text>'
                      for i, t in enumerate(notes)))
    return svg.replace("</svg>", pre + head + "\n</svg>")


def poly(pts, color, width, dash=None, opacity=0.9, cap="round"):
    p = " ".join(f"{mp.sx(x):.0f},{mp.sy(y):.0f}" for x, y, *_ in pts)
    d = f' stroke-dasharray="{dash}"' if dash else ""
    return (f'<polyline points="{p}" fill="none" stroke="{color}" stroke-width="{width}" '
            f'stroke-linecap="{cap}" stroke-linejoin="round" opacity="{opacity}"{d}/>')


def text(x, y, t, size=190, color="#222", anchor="middle", weight=700, rot=None, halo=True):
    tr = f' transform="rotate({rot} {mp.sx(x)} {mp.sy(y)})"' if rot else ""
    h = ' paint-order="stroke" stroke="#fff" stroke-width="45" stroke-linejoin="round"' if halo else ""
    return (f'<text x="{mp.sx(x)}" y="{mp.sy(y)}" font-size="{size}" fill="{color}" text-anchor="{anchor}" '
            f'font-weight="{weight}"{h}{tr}>{t}</text>')


def shaft_svg(s, label=True, faded=False):
    x0, x1, y0, y1 = s["rect"]
    o = [f'<rect x="{mp.sx(x0)}" y="{mp.sy(y1)}" width="{x1 - x0}" height="{y1 - y0}" fill="#cfd6db" '
         f'stroke="#33414b" stroke-width="22" opacity="{0.5 if faded else 1}"/>',
         f'<line x1="{mp.sx(x0)}" y1="{mp.sy(y1)}" x2="{mp.sx(x1)}" y2="{mp.sy(y0)}" stroke="#33414b" stroke-width="14"/>',
         f'<line x1="{mp.sx(x0)}" y1="{mp.sy(y0)}" x2="{mp.sx(x1)}" y2="{mp.sy(y1)}" stroke="#33414b" stroke-width="14"/>']
    return "".join(o)


def grille_svg(g):
    x, y = g["pos"][:2]
    nx, ny = g["n"]
    w, t = 250, 70
    if nx == 0:
        r = (x - w / 2, x + w / 2, y if ny > 0 else y - t, y + t if ny > 0 else y)
    else:
        r = (x if nx > 0 else x - t, x + t if nx > 0 else x, y - w / 2, y + w / 2)
    c = COL[g["type"]]
    o = f'<rect x="{mp.sx(r[0])}" y="{mp.sy(r[3])}" width="{r[1] - r[0]}" height="{r[3] - r[2]}" fill="{c}" stroke="#1c2830" stroke-width="10"/>'
    # стрелка направления воздуха
    ax, ay = x + nx * 120, y + ny * 120
    bx, by = x + nx * 520, y + ny * 520
    if g["type"] == "eta":
        ax, ay, bx, by = bx, by, ax, ay
    o += (f'<line x1="{mp.sx(ax)}" y1="{mp.sy(ay)}" x2="{mp.sx(bx)}" y2="{mp.sy(by)}" stroke="{c}" '
          f'stroke-width="28" marker-end="url(#arr-{g["type"]})"/>')
    if nx:
        lx, ly = x + nx * 700, y + 230
    else:
        lx, ly = x, y + ny * 1250
    o += text(lx, ly, f'{NAME[g["type"]]} {g["flow"]}', 200, c)
    return o


WIRE = {"power": ("#c0392b", 55, None), "lv": (PURPLE, 38, "140 90"), "heat": ("#e67e22", 45, "60 60")}


def marker(x, y, n, reserve=False):
    op = 0.5 if reserve else 1
    return (f'<circle cx="{mp.sx(x)}" cy="{mp.sy(y)}" r="190" fill="#fff" stroke="{PURPLE}" stroke-width="45" opacity="{op}"/>'
            f'<text x="{mp.sx(x)}" y="{mp.sy(y) + 72}" font-size="210" font-weight="700" fill="{PURPLE}" '
            f'text-anchor="middle" opacity="{op}">{n}</text>')


def wire_svg(wi, faded=False):
    color, width, dash = WIRE[wi["kind"]]
    pts = wi["pts"]
    if len(pts) < 2:
        return ""
    return poly(pts, color, width, dash=("200 150" if wi.get("reserve") else dash), opacity=0.35 if faded else 0.95)


def elec_marker_pos(e):
    """Смещение номера от точки, чтобы не закрывать стену."""
    x, y = e["pos"][:2]
    nx, ny = e.get("nrm") or [0, 0]
    return x + nx * 420, y + ny * 420


DEFS = "".join(
    f'<marker id="arr-{k}" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="4" markerHeight="4" orient="auto-start-reverse">'
    f'<path d="M0,0 L10,5 L0,10 z" fill="{c}"/></marker>' for k, c in COL.items())


def legend(y, items):
    o = []
    x = -205
    for color, label, kind in items:
        if kind == "line":
            o.append(f'<line x1="{mp.sx(x)}" y1="{mp.sy(y) - 70}" x2="{mp.sx(x + 600)}" y2="{mp.sy(y) - 70}" stroke="{color}" stroke-width="120" stroke-linecap="round"/>')
        elif kind == "dash":
            o.append(f'<line x1="{mp.sx(x)}" y1="{mp.sy(y) - 70}" x2="{mp.sx(x + 600)}" y2="{mp.sy(y) - 70}" stroke="{color}" stroke-width="90" stroke-dasharray="150 110"/>')
        elif kind == "shaft":
            o.append(shaft_svg({"rect": [x + 150, x + 450, y - 220, y + 80]}))
        elif kind == "dot":
            o.append(f'<circle cx="{mp.sx(x + 300)}" cy="{mp.sy(y) - 70}" r="110" fill="{color}"/>')
        o.append(text(x + 750, y - 150, label, 210, "#333", "start", 400, halo=False))
        x += 750 + len(label) * 118 + 500
    return "".join(o)


# ------------------------------------------------------------------ 2-й этаж
def sheet_floor2():
    svg = base(2, "ВЕНТИЛЯЦИЯ СПАЛЕН — 2-й ЭТАЖ (отм. +3,300)", [
        "Трубы — в подшивном потолке санузлов и кладовых (низ потолка 2,75 м). Решётки — в стенах спален, центр на 2,90 м от пола.",
        "Все отводы к решёткам — гофра Ø125, магистрали с кровли — Ø160. Размеры привязок — в см, для левой половины; правая зеркальна.",
    ])
    o = [f"<defs>{DEFS}</defs>"]
    for side in (L, R):
        for d in side["ducts"]:
            if d["zone"] == "ceil2":
                o.append(poly(d["pts"], COL[d["type"]], d["d"]))
        for d in side["ducts"]:     # точки опуска с кровли
            if d["zone"] == "roof" and d.get("to"):
                x, y = d["pts"][-1][:2]
                o.append(f'<circle cx="{mp.sx(x)}" cy="{mp.sy(y)}" r="{d["d"] / 2}" fill="#fff" stroke="{COL[d["type"]]}" stroke-width="40"/>')
        for s in side["shafts"]:
            if not s.get("reserve"):
                o.append(shaft_svg(s))
        for g in side["grilles"]:
            if not g.get("reserve"):
                o.append(grille_svg(g))
        for e in side["elec"]:
            if e["kind"] in ("sensor", "pult") and not e.get("reserve"):
                mx, my = elec_marker_pos(e)
                o.append(marker(mx, my, e["n"]))
    # подписи шахт и труб (левая и правая)
    for side in (L, R):
        sh = [s for s in side["shafts"] if not s.get("reserve")]
        for s in sh:
            x0, x1, y0, y1 = s["rect"]
            cx = (x0 + x1) / 2
            if s["id"] == "А":   # подпись снаружи дома, с выноской
                left = cx < 14850
                tx = -1100 if left else 30150
                o.append(f'<line x1="{mp.sx(x0 if left else x1)}" y1="{mp.sy((y0 + y1) / 2)}" x2="{mp.sx(tx)}" y2="{mp.sy((y0 + y1) / 2)}" stroke="#1c2830" stroke-width="12"/>')
                o.append(text(tx + (-60 if left else 60), (y0 + y1) / 2 - 70, s["name"], 210, "#1c2830", "end" if left else "start"))
            else:
                o.append(text(cx + (-700 if cx < 14850 else 700), y0 - 300, s["name"], 210, "#1c2830"))
    # привязки решёток (левая половина)
    zl = L
    g = {(x["room"], x["type"]): x for x in zl["grilles"]}
    o.append(mp.dim_h(200, g[("R", "sup")]["pos"][0], 4855 - 600))
    o.append(mp.dim_h(g[("R", "sup")]["pos"][0], g[("R", "eta")]["pos"][0], 4855 - 600))
    o.append(mp.dim_h(200, g[("D1", "sup")]["pos"][0], 8520 + 700))
    o.append(mp.dim_h(g[("D1", "sup")]["pos"][0], g[("D1", "eta")]["pos"][0], 8520 + 700))
    o.append(mp.dim_v(11400 + 800, g[("D2", "sup")]["pos"][1], 12000))
    o.append(mp.dim_v(11400 + 800, g[("D2", "eta")]["pos"][1], g[("D2", "sup")]["pos"][1]))
    o.append(legend(-1650, [(COL["sup"], "приток в спальню", "line"), (COL["eta"], "вытяжка из спальни", "line"),
                            ("#33414b", "шахта (короб с гофрой)", "shaft"), (PURPLE, "электроточки — см. лист «Электрика»", "dot")]))
    o.append(text(-205, -2350, "○ — место опуска трубы с кровли (проходка через перекрытие Ø200). "
                  "П/В 120 — приток/вытяжка, м³/ч.", 210, "#444", "start", 400, halo=False))
    return svg.replace("</svg>", "\n".join(o) + "\n</svg>")


# ------------------------------------------------------------------ кровля
def sheet_roof():
    fade = f'<rect x="0" y="0" width="{mp.VB[2] - mp.VB[0]}" height="{mp.VB[3] - mp.VB[1]}" fill="#fff" opacity="0.55"/>'
    svg = base(2, "ВЕНТИЛЯЦИЯ — КРОВЛЯ: РЕКУПЕРАТОРЫ И ВОЗДУХОВОДЫ", [
        "Рекуператоры стоят над лестницами (не над спальнями), на раме с виброопорами. Трубы на кровле — в утеплителе 50 мм и защитном кожухе.",
        "Забор воздуха — колпак сеткой вниз, низ ≥ 1 м над кровлей. Выброс — на 1 м выше забора и в 3,5–4 м от него.",
    ], pre=fade)
    o = [f"<defs>{DEFS}</defs>"]
    for side in (L, R):
        for d in side["ducts"]:
            if d["zone"] == "roof":
                o.append(poly(d["pts"], "#1c2830", d["d"] + 140, opacity=0.25))
                o.append(poly(d["pts"], COL[d["type"]], d["d"]))
        for s in side["shafts"]:
            if not s.get("reserve"):
                o.append(shaft_svg(s))
        u = side["unit"]
        x0, x1, y0, y1 = u["rect"]
        o.append(f'<rect x="{mp.sx(x0)}" y="{mp.sy(y1)}" width="{x1 - x0}" height="{y1 - y0}" fill="#eef1f3" stroke="#1c2830" stroke-width="40"/>')
        o.append(text((x0 + x1) / 2, (y0 + y1) / 2 + 40, u["name"], 200, "#1c2830", halo=False))
        o.append(text((x0 + x1) / 2, (y0 + y1) / 2 - 220, f'1000 м³/ч · расчёт {side["total"]}', 160, "#444", weight=400, halo=False))
        for d in side["ducts"]:
            if d["type"] in ("oda", "eha"):
                x, y = d["pts"][-1][:2]
                o.append(f'<circle cx="{mp.sx(x)}" cy="{mp.sy(y)}" r="260" fill="{COL[d["type"]]}" stroke="#1c2830" stroke-width="20"/>')
                h = (d["pts"][-1][2] - vent.ROOF) / 1000
                lbl = f'{"забор" if d["type"] == "oda" else "выброс"} Ø{d["d"]}, +{str(h).replace(".", ",")} м'
                o.append(text(x, y + (-560 if d["type"] == "oda" else 420), lbl, 190, COL[d["type"]]))
        for wi in side["wires"]:
            if wi["pts"][-1][2] > vent.ROOF and wi["pts"][0][2] > vent.FL2 and wi["kind"] != "lv":
                o.append(wire_svg(wi))
        for e in side["elec"]:
            if e["kind"] in ("riser", "isolator", "socket", "heat"):
                o.append(marker(*e["pos"][:2], e["n"]))
        # подписи трасс
        for d in side["ducts"]:
            if d["zone"] == "roof" and d.get("to") and d["type"] == "sup":
                p0, p1 = d["pts"][0], d["pts"][1]
                if d["to"] == "Б":
                    o.append(text((p0[0] + p1[0]) / 2, p0[1] + 330, f'П+В 2×Ø160 → шахта Б-{side["tag"]}', 180, "#1c2830"))
                else:
                    pa, pb = d["pts"][2], d["pts"][3]
                    o.append(text((pa[0] + pb[0]) / 2, pa[1] - 420, f'П+В 2×Ø160 → шахта А-{side["tag"]}', 180, "#1c2830"))
    # привязка рекуператора Л к внутренним граням лестничной клетки
    x0, x1, y0, y1 = L["unit"]["rect"]
    o.append(mp.dim_h(4600, x0, y1 + 450))
    o.append(mp.dim_v(x1 + 450, 8150, y0))
    o.append(legend(-1650, [(COL["sup"], "приток", "line"), (COL["eta"], "вытяжка", "line"),
                            (COL["oda"], "забор наружного воздуха", "dot"), (COL["eha"], "выброс", "dot"),
                            (PURPLE, "электроточки (номера — лист «Электрика»)", "dot")]))
    o.append(text(-205, -2350, "Привязка рекуператора — от внутренних граней стен лестничной клетки, см. Правый — зеркально.",
                  210, "#444", "start", 400, halo=False))
    return svg.replace("</svg>", "\n".join(o) + "\n</svg>")


# ------------------------------------------------------------------ 1-й этаж (резерв)
def sheet_floor1():
    svg = base(1, "ВЕНТИЛЯЦИЯ — 1-й ЭТАЖ: РЕЗЕРВ ПОД СПАЛЬНЮ", [
        "Делается, только если центральная комната 1-го этажа станет спальней. Шахта Б продолжается вниз до потолка санузла.",
        "Если не сейчас — оставьте в перекрытии гильзу 2×Ø150 под шахтой Б и заглушите.",
    ])
    o = [f"<defs>{DEFS}</defs>"]
    for side in (L, R):
        for d in side["ducts"]:
            if d["zone"] == "ceil1":
                o.append(poly(d["pts"], COL[d["type"]], d["d"], dash="260 160"))
        for s in side["shafts"]:
            if s.get("reserve"):
                o.append(shaft_svg(s, faded=True))
                x0, x1, y0, y1 = s["rect"]
                cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
                tx = cx + (1700 if cx < 14850 else -1700)
                o.append(f'<line x1="{mp.sx(cx)}" y1="{mp.sy(cy)}" x2="{mp.sx(tx)}" y2="{mp.sy(8600)}" stroke="#1c2830" stroke-width="12"/>')
                o.append(text(tx, 8350, s["name"] + " (резерв)", 200, "#1c2830"))
        for g in side["grilles"]:
            if g.get("reserve"):
                o.append(grille_svg(g))
    g = {(x["room"], x["type"]): x for x in L["grilles"]}
    o.append(mp.dim_v(10900 + 420, g[("K1", "sup")]["pos"][1], 12000))
    o.append(mp.dim_v(10900 + 420, g[("K1", "eta")]["pos"][1], g[("K1", "sup")]["pos"][1]))
    o.append(legend(-1650, [(COL["sup"], "приток (резерв)", "dash"), (COL["eta"], "вытяжка (резерв)", "dash"),
                            ("#33414b", "шахта Б (продолжение)", "shaft")]))
    o.append(text(-205, -2350, "Центр решёток — 2,90 м от пола 1-го этажа. Размеры в см.", 210, "#444", "start", 400, halo=False))
    return svg.replace("</svg>", "\n".join(o) + "\n</svg>")


# ------------------------------------------------------------------ электрика
def sheet_elec():
    fade = f'<rect x="0" y="0" width="{mp.VB[2] - mp.VB[0]}" height="{mp.VB[3] - mp.VB[1]}" fill="#fff" opacity="0.45"/>'
    svg = base(2, "ЭЛЕКТРИКА ДЛЯ ВЕНТИЛЯЦИИ — 2-й ЭТАЖ И КРОВЛЯ", [
        "Номера точек — как в таблице «Электрика» (последний лист). Правая половина — зеркально, номера те же.",
        "Красное — силовые кабели, фиолетовое — слаботочные (витая пара), оранжевое — греющий кабель дренажа. Пунктир на кровле — кабели в гофре/металлорукаве.",
    ], pre=fade)
    o = [f"<defs>{DEFS}</defs>"]
    for side in (L, R):
        for d in side["ducts"]:          # трубы — бледным фоном
            if d["zone"] in ("ceil2", "roof") and d["type"] in ("sup", "eta"):
                o.append(poly(d["pts"], COL[d["type"]], d["d"], opacity=0.18))
        for s in side["shafts"]:
            if not s.get("reserve"):
                o.append(shaft_svg(s, faded=True))
        u = side["unit"]
        x0, x1, y0, y1 = u["rect"]
        o.append(f'<rect x="{mp.sx(x0)}" y="{mp.sy(y1)}" width="{x1 - x0}" height="{y1 - y0}" fill="#fff" fill-opacity=".7" '
                 f'stroke="#1c2830" stroke-width="30" stroke-dasharray="120 80"/>')
        o.append(text((x0 + x1) / 2, (y0 + y1) / 2 - 60, "рекуператор", 170, "#1c2830", weight=600))
        o.append(text((x0 + x1) / 2, (y0 + y1) / 2 - 260, "(на кровле)", 150, "#555", weight=400))
        for wi in side["wires"]:
            if not wi.get("reserve"):
                o.append(wire_svg(wi))
        for e in side["elec"]:
            if e.get("reserve"):
                continue
            mx, my = elec_marker_pos(e) if e["kind"] in ("sensor", "pult") else e["pos"][:2]
            if e["kind"] == "riser":
                mx += 0
            o.append(marker(mx, my, e["n"]))
    o.append(legend(-1650, [("#c0392b", "силовой кабель (линии 1 и 2)", "line"), (PURPLE, "витая пара (пульт, датчики)", "dash"),
                            ("#e67e22", "греющий кабель дренажа", "line"), (PURPLE, "точка — номер в таблице", "dot")]))
    o.append(text(-205, -2350, "1 — стояк от щита идёт с 1-го этажа (штроба у оси 1) через шахту А на кровлю. "
                  "Все подрозетники — на 1,5 м от пола.", 210, "#444", "start", 400, halo=False))
    return svg.replace("</svg>", "\n".join(o) + "\n</svg>")


# ------------------------------------------------------------------ разрез и спецификация
def section_svg():
    """Схематичный разрез: детская | стена | с/у с подшивным потолком | кровля с рекуператором (не в масштабе по X)."""
    W, H = 1500, 900
    k = 0.12            # px на мм по высоте
    base_y = 860        # пол 2-го этажа

    def Y(z):
        return base_y - (z - vent.FL2) * k

    c = vent.C2
    g = []
    g.append(f'<svg viewBox="0 0 {W} {H}" font-family="DejaVu Sans, Arial, sans-serif" font-size="21">')
    g.append(f'<defs>{DEFS}</defs>')
    # перекрытия
    g.append(f'<rect x="40" y="{Y(vent.ROOF)}" width="1180" height="{Y(c) - Y(vent.ROOF)}" fill="#b8b2a8"/>')
    g.append(f'<rect x="40" y="{Y(vent.FL2)}" width="1180" height="22" fill="#b8b2a8"/>')
    # стена между детской и с/у
    g.append(f'<rect x="560" y="{Y(c)}" width="26" height="{Y(vent.FL2) - Y(c)}" fill="#3a3a3a"/>')
    # подшивной потолок в с/у
    g.append(f'<line x1="586" y1="{Y(vent.FL2 + 2750)}" x2="1000" y2="{Y(vent.FL2 + 2750)}" stroke="#555" stroke-width="3" stroke-dasharray="8 5"/>')
    g.append(f'<text x="790" y="{Y(vent.FL2 + 2750) + 26}" text-anchor="middle" fill="#555">подшивной потолок с/у, 2,75 м</text>')
    # шахта и трубы
    zc = vent.Z_CEIL2
    g.append(f'<rect x="930" y="{Y(vent.ROOF)}" width="70" height="{Y(zc - 150) - Y(vent.ROOF)}" fill="#cfd6db" stroke="#33414b" stroke-width="2"/>')
    g.append(f'<polyline points="965,{Y(vent.Z_ROOFDUCT)} 965,{Y(zc)} 560,{Y(zc)} 520,{Y(zc)}" fill="none" stroke="{COL["sup"]}" stroke-width="11" stroke-linejoin="round"/>')
    g.append(f'<polyline points="965,{Y(vent.Z_ROOFDUCT)} 1180,{Y(vent.Z_ROOFDUCT)}" fill="none" stroke="#1c2830" stroke-opacity=".25" stroke-width="22"/>')
    g.append(f'<polyline points="965,{Y(vent.Z_ROOFDUCT)} 1180,{Y(vent.Z_ROOFDUCT)}" fill="none" stroke="{COL["sup"]}" stroke-width="11"/>')
    # решётка
    g.append(f'<rect x="540" y="{Y(zc) - 8}" width="20" height="16" fill="{COL["sup"]}" stroke="#1c2830"/>')
    g.append(f'<line x1="535" y1="{Y(zc)}" x2="420" y2="{Y(zc)}" stroke="{COL["sup"]}" stroke-width="4" marker-end="url(#arr-sup)"/>')
    # рекуператор
    g.append(f'<rect x="1180" y="{Y(vent.ROOF + 150 + vent.UNIT_H)}" width="200" height="{vent.UNIT_H * k}" fill="#eef1f3" stroke="#1c2830" stroke-width="2"/>')
    g.append(f'<text x="1280" y="{Y(vent.ROOF + 150 + vent.UNIT_H / 2) + 7}" text-anchor="middle" font-weight="700" font-size="19">рекуператор</text>')
    g.append(f'<line x1="1190" y1="{Y(vent.ROOF)}" x2="1190" y2="{Y(vent.ROOF + 150)}" stroke="#333" stroke-width="5"/>')
    g.append(f'<line x1="1370" y1="{Y(vent.ROOF)}" x2="1370" y2="{Y(vent.ROOF + 150)}" stroke="#333" stroke-width="5"/>')
    # забор / выброс
    g.append(f'<polyline points="1240,{Y(vent.ROOF + 450)} 1120,{Y(vent.ROOF + 450)} 1120,{Y(vent.ROOF + 1000)}" fill="none" stroke="{COL["oda"]}" stroke-width="13"/>')
    g.append(f'<path d="M1095,{Y(vent.ROOF + 1000)} h50 l-25,-22 z" fill="{COL["oda"]}" transform="rotate(180 1120 {Y(vent.ROOF + 1000) - 6})"/>')
    g.append(f'<polyline points="1330,{Y(vent.ROOF + 450)} 1440,{Y(vent.ROOF + 450)} 1440,{Y(vent.ROOF + 2000)}" fill="none" stroke="{COL["eha"]}" stroke-width="13"/>')
    g.append(f'<path d="M1415,{Y(vent.ROOF + 2000)} h50 l-25,-22 z" fill="{COL["eha"]}"/>')
    g.append(f'<text x="1090" y="{Y(vent.ROOF + 1000) - 10}" text-anchor="end" fill="{COL["oda"]}" font-weight="700">забор ≥ 1 м над кровлей</text>')
    g.append(f'<text x="1430" y="{Y(vent.ROOF + 2000) - 30}" text-anchor="end" fill="{COL["eha"]}" font-weight="700">выброс ≥ на 1 м выше</text>')

    # отметки
    def mark(z, label, x=30, dy=-8):
        g.append(f'<line x1="{x}" y1="{Y(z)}" x2="{x + 18}" y2="{Y(z)}" stroke="#c0392b" stroke-width="3"/>')
        g.append(f'<text x="{x + 24}" y="{Y(z) + dy}" fill="#c0392b" font-weight="700">{label}</text>')
    mark(vent.FL2, "0,00 пол 2-го эт.", 60)
    mark(zc, "2,90 ось трубы и решётки", 60, 26)
    mark(c, "3,05 потолок спальни", 60, -26)
    g.append(f'<text x="300" y="{Y(vent.FL2 + 1300)}" text-anchor="middle" font-size="18" font-weight="700" fill="#555">СПАЛЬНЯ</text>')
    g.append(f'<text x="300" y="{Y(vent.FL2 + 1300) + 22}" text-anchor="middle" fill="#555">потолок не опускается</text>')
    g.append(f'<text x="790" y="{Y(vent.FL2 + 1300)}" text-anchor="middle" font-size="18" font-weight="700" fill="#555">САНУЗЕЛ / КЛАДОВАЯ</text>')
    g.append(f'<text x="965" y="{Y(vent.FL2 + 2300)}" text-anchor="middle" fill="#33414b">шахта</text>')
    g.append(f'<text x="573" y="{Y(vent.FL2 + 600)}" text-anchor="middle" fill="#fff" font-size="11" transform="rotate(-90 573 {Y(vent.FL2 + 600)})">стена</text>')
    g.append(f'<text x="300" y="{Y(zc) + 34}" fill="{COL["sup"]}" font-weight="700">решётка, жалюзи вдоль потолка</text>')
    g.append(f'<text x="760" y="{Y(zc) - 10}" fill="{COL["sup"]}" font-weight="700">гофра Ø125</text>')
    g.append("</svg>")
    return "".join(g)


def spec_html():
    rows_rooms = "".join(
        f'<tr{" class=res" if r["reserve"] else ""}><td>{r["name"]}</td><td>{r["people"]}</td><td class=n>{str(r["area"]).replace(".", ",")}</td>'
        f'<td class=n>{r["flow"]}</td><td class=n>{r["flow"]}</td><td>Ø125</td></tr>' for r in L["rooms"])
    gr = {(x["room"], x["type"]): x for x in L["grilles"]}

    def gline(rid):
        s, e = gr[(rid, "sup")], gr[(rid, "eta")]
        return (f'<tr><td>{next(r["name"] for r in L["rooms"] if r["id"] == rid)}</td><td>{s["wall"]}</td>'
                f'<td class=n>{round(s["off"] / 10)}</td><td class=n>{round(e["off"] / 10)}</td><td>{s["from"]}</td></tr>')
    rows_grilles = "".join(gline(r) for r in ("R", "D1", "D2", "K1"))
    rows_elec = "".join(
        f'<tr{" class=res" if e.get("reserve") else ""}><td class=n>{e["n"]}</td><td>{e["name"]}</td>'
        f'<td>{e["where"]}; {e["h"]}</td><td>{e["cable"]}</td></tr>' for e in L["elec"])
    return f"""<!doctype html><html lang="ru"><head><meta charset="utf-8"><title>Вентиляция — спецификация</title>
<style>
@page{{size:A3 landscape;margin:12mm}}
body{{font-family:"DejaVu Sans",Arial,sans-serif;color:#1c2830;font-size:9.5pt;margin:0}}
h1{{font-size:20pt;margin:0 0 4mm}}
h2{{font-size:12.5pt;margin:5mm 0 2mm;text-transform:uppercase;letter-spacing:.04em;color:#444}}
.grid{{display:grid;grid-template-columns:1.1fr 1fr 1.1fr;gap:7mm}}
table{{border-collapse:collapse;width:100%;font-size:8.6pt}}
th,td{{border:1px solid #c9d1d6;padding:3px 6px;text-align:left;vertical-align:top}}
th{{background:#eef1f3;font-weight:600}}
td.n{{text-align:right;font-variant-numeric:tabular-nums}}
tr.res td{{color:#777}}
ul{{margin:0;padding-left:5mm}} li{{margin:1mm 0}}
.muted{{color:#666;font-size:8.3pt}}
svg{{display:block;width:100%;height:60mm}}
h2{{margin-top:3.5mm}}
</style></head><body>
<h1>Вентиляция спален: разрез, спецификация, электрика</h1>
<p class="muted">Два рекуператора по 1000 м³/ч на кровле, по одному на каждую половину дома (половины зеркальны). Приточно-вытяжная система только для спален. Все цифры — на ОДНУ половину дома, на весь дом ×2.</p>
<div class="grid">
<div>
<h2>Разрез: спальня — санузел — кровля (схема)</h2>
{section_svg()}
<h2>Расходы воздуха (одна половина)</h2>
<table><tr><th>Помещение</th><th>Чел.</th><th>м²</th><th>Приток, м³/ч</th><th>Вытяжка, м³/ч</th><th>Труба</th></tr>
{rows_rooms}
<tr><td><b>Итого на рекуператор</b></td><td></td><td></td><td class=n><b>{L["total"]}</b></td><td class=n><b>{L["total"]}</b></td><td>магистрали Ø160</td></tr>
<tr class=res><td>С резервом 1-го этажа</td><td></td><td></td><td class=n>{L["totalWithReserve"]}</td><td class=n>{L["totalWithReserve"]}</td><td></td></tr></table>
<p class="muted">Расчёт: 60 м³/ч на спящего человека (CO₂ ниже ~900 ppm при закрытой двери), не меньше одного обмена в час и не меньше 90 м³/ч на спальню. Скорость в Ø125 — до 2,7 м/с, в Ø160 — до 2,9 м/с (тихо). Рекуператор 1000 м³/ч работает на 33–45% — с большим запасом; по расчёту хватило бы агрегата на 500–600 м³/ч.</p>
<h2>Забор и выброс воздуха</h2>
<ul>
<li><b>Забор</b> — колпак сеткой вниз, низ не ниже 1 м над кровлей (пыль, жар от покрытия летом, снег), со стороны двора.</li>
<li><b>Выброс</b> — вертикальный дефлектор на 1 м выше забора и в 3,5–4 м от него, в сторону внутреннего дворика.</li>
<li>Забор не ближе 8 м от дымохода котла (котельная может быть во внутреннем дворике у оси Г), от выхода кухонной вытяжки и не ближе 3 м от фановых стояков (лучше выше них).</li>
<li>Фильтры: приток — F7 (пыль, пыльца), вытяжка — G4/M5. Рекуператор нужен в уличном исполнении или в утеплённом коробе, с электроподогревателем и дренажом.</li>
<li>Рекуператор стоит над лестницей, а не над спальнями (вибрация, шум). Раму опереть на несущие стены лестничной клетки, на виброопорах.</li>
</ul>
<h2>Чего эта схема не делает</h2>
<ul><li>Санузлы и кухня вентилируются отдельно (свои вытяжные вентиляторы и трубы на кровлю); их выходы — не ближе 3 м от забора рекуператора.</li></ul>
</div>
<div>
<h2>Решётки (центр на 2,90 м от пола)</h2>
<table><tr><th>Спальня</th><th>Стена</th><th>Приток, см от угла</th><th>Вытяжка, см от угла</th><th>Угол отсчёта</th></tr>{rows_grilles}</table>
<p class="muted">Отверстие в стене Ø150 (под гофру Ø125 с уплотнением). Приток — решётка 200×100 с регулируемыми жалюзи, направить вдоль потолка в комнату; вытяжка — простая решётка 200×100. В комнате родителей решётки всего в 1 м друг от друга (короткая стена до двери санузла) — приток обязательно направить от стены в глубину комнаты.</p>
<h2>Шахты и трубы</h2>
<ul>
<li><b>Шахта А</b> — в кладовой, в углу у наружной стены (короб 40×30 см): 2 трубы Ø160 с кровли. В потолке кладовой — тройники: на детскую (крыло) и через потолок санузла на комнату родителей.</li>
<li><b>Шахта Б</b> — в общем санузле, у стены детской (короб 30×50 см): 2 трубы Ø160 с кровли → детская (центр). При резерве продолжается вниз в санузел 1-го этажа.</li>
<li>Внутри дома — гибкие гофрированные трубы; лучше полужёсткие с гладкой внутренней стенкой. Каждый отвод — не длиннее 3–4 м, натянут без провисов, поворотов минимум.</li>
<li>На каждом отводе — ирисовый клапан для настройки расхода, доступ через лючок в подшивном потолке санузла или кладовой.</li>
<li>Шумоглушители Ø160 длиной 1 м на притоке и вытяжке сразу под кровлей (в шахте или потолке кладовой). Решётки двух спален с общей магистрали разнести так, чтобы между ними было ≥ 1,5 м трубы — меньше «переговоров» между комнатами.</li>
<li>На кровле — трубы в утеплителе 50 мм с металлическим кожухом, на опорах 15–25 см. Проходки через кровлю — заводские, с герметизацией.</li>
</ul>
</div>
<div>
<h2>Электрика — что оставить (на каждую половину дома)</h2>
<table><tr><th>№</th><th>Что</th><th>Где, высота</th><th>Кабель</th></tr>{rows_elec}</table>
<h2>В щите (на каждый рекуператор)</h2>
<table><tr><th>Линия</th><th>Автомат</th><th>Кабель</th><th>Куда</th></tr>
<tr><td>1. Рекуператор</td><td>по паспорту агрегата (обычно 1P C16–C25 или 3P C16)</td><td>5×4 мм²</td><td>выключатель IP65 на раме (2)</td></tr>
<tr><td>2. Розетка и обогрев дренажа</td><td>дифавтомат 1P C16, 30 мА</td><td>3×2,5 мм²</td><td>розетка IP65 (3) и коробка греющего кабеля (4)</td></tr></table>
<p class="muted">В каждой шахте — ещё пустая гофра Ø32 с протяжкой на запас. Слаботочные кабели ведите отдельно от силовых (не в одной гофре). Точное сечение и номинал автомата — по паспорту выбранной модели. Без электроподогревателя агрегату хватает 3×2,5 мм², но в Ташкенте зимой бывает −10…−15 °C, и пластинчатый рекуператор без подогрева обмерзает — поэтому кабель с запасом.</p>
</div></div></body></html>"""


if __name__ == "__main__":
    os.makedirs(mp.OUT, exist_ok=True)
    for name, fn in (("vent-1-etazh-2.svg", sheet_floor2), ("vent-2-krovlya.svg", sheet_roof),
                     ("vent-3-etazh-1.svg", sheet_floor1), ("vent-5-elektrika.svg", sheet_elec)):
        with open(os.path.join(mp.OUT, name), "w", encoding="utf-8") as fh:
            fh.write(fn())
        print("ok", name)
    with open(os.path.join(mp.OUT, "vent-4-spec.html"), "w", encoding="utf-8") as fh:
        fh.write(spec_html())
    print("ok spec")

"""Чертежи вентиляции спален (для строителей и электрика).

plan/vent-1-etazh-2.svg  — 2-й этаж: шахты, трубы в подшивных потолках, решётки с привязками
plan/vent-2-krovlya.svg  — задний двор: рекуператоры, короб на фасаде, забор и выброс (кровлю не сверлим)
plan/vent-6-fasad.html   — фасад со двора и разрез: как трубы входят в дом сквозь стену
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


def base(floor, title, notes=(), pre="", drop_yard=False):
    svg = mp.build(floor)
    if drop_yard:   # подписи «внутренний дворик» мешают рекуператору
        svg = re.sub(r'<text class="(name|sub|small)"[^>]*>(Внутр\. дворик \(открыт\)|Дворик / котельная)</text>', "", svg)
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
    o += text(lx, ly, f'{NAME[g["type"]]} {g["flow"]}' + (" ↑" if g["type"] == "sup" else " ↓"), 200, c)
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


def callout(side, lines, anchor_pts):
    """Текстовый блок во дворе между крыльями + выносные линии к точкам во дворе."""
    left = side["side"] == "L"
    bx = 5000 if left else 15400
    by = 5900
    o = [f'<rect x="{mp.sx(bx - 200)}" y="{mp.sy(by + 350)}" width="9300" height="{len(lines) * 330 + 300}" '
         f'fill="#fff" stroke="#1c2830" stroke-width="18" rx="60"/>']
    for i, (t, color, w) in enumerate(lines):
        o.append(text(bx, by - i * 330, t, 190, color, "start", w, halo=False))
    for (x, y) in anchor_pts:
        o.append(f'<line x1="{mp.sx(x)}" y1="{mp.sy(y)}" x2="{mp.sx(bx + (1500 if left else 7600))}" y2="{mp.sy(by + 350)}" '
                 f'stroke="#1c2830" stroke-width="14" stroke-dasharray="60 40"/>')
    return "".join(o)


def yard_lines(side):
    t = side["tag"]
    return [(f"Задний двор ({t}): рекуператор 1000 м³/ч, 140×85 см", "#1c2830", 700),
            ("стоит у стены по оси Г, 25 см от двери во двор, на подушке", "#333", 400),
            ("забор Ø250 — колпак сеткой вниз, 2,0 м от земли", COL["oda"], 700),
            ("выброс Ø250 — в коробе по фасаду, снаружи на 1,0 м выше кровли", COL["eha"], 700),
            ("приток/вытяжка Ø200 — в коробе вверх до 2-го эт., сквозь стену Г", "#333", 400)]


def box_svg(b, faded=False):
    return poly(b["pts"], "#cfd6db", b["w"], opacity=0.45 if faded else 0.9, cap="butt")


def hole_svg(h):
    x, y = h["pos"][:2]
    if h.get("cable"):
        return (f'<circle cx="{mp.sx(x)}" cy="{mp.sy(y)}" r="60" fill="{PURPLE}" stroke="#fff" stroke-width="14"/>')
    return (f'<circle cx="{mp.sx(x)}" cy="{mp.sy(y)}" r="{h["d"] / 2 + 30}" fill="#fff" fill-opacity=".85" '
            f'stroke="#111" stroke-width="22"/>')


def node_svg(s):
    x0, x1, y0, y1 = s["rect"]
    return (f'<rect x="{mp.sx(x0)}" y="{mp.sy(y1)}" width="{x1 - x0}" height="{y1 - y0}" fill="none" '
            f'stroke="#33414b" stroke-width="22" stroke-dasharray="80 50"/>')


def unit_svg(side, faded=False):
    u = side["unit"]["rect"]
    r = side["riser"]["rect"]
    op = 0.55 if faded else 1
    return (f'<rect x="{mp.sx(r[0])}" y="{mp.sy(r[3])}" width="{r[1] - r[0]}" height="{r[3] - r[2]}" fill="#e3e7ea" '
            f'stroke="#33414b" stroke-width="25" opacity="{op}"/>'
            f'<rect x="{mp.sx(u[0])}" y="{mp.sy(u[3])}" width="{u[1] - u[0]}" height="{u[3] - u[2]}" fill="#eef1f3" '
            f'stroke="#1c2830" stroke-width="35" opacity="{op}"/>'
            + text((u[0] + u[1]) / 2, (u[2] + u[3]) / 2 - 70, "Р-" + side["tag"], 220, "#1c2830", halo=False))


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
        "Кровлю не сверлим. Трубы входят в дом сквозь стену Г со двора и идут в коробе под потолком лестницы, холла и коридора к узлам в кладовой (А) и санузле (Б).",
        "Решётки: приток П↑ — под потолком (центр 2,90 м), вытяжка В↓ — внизу (0,30 м). Привязки — в см, для левой половины; правая зеркальна.",
    ], drop_yard=True)
    o = [f"<defs>{DEFS}</defs>"]
    for side in (L, R):
        for b in side["boxes"]:
            o.append(box_svg(b))
        o.append(unit_svg(side, faded=True))
        for t in ("eta", "sup"):            # вытяжка ниже, приток поверх
            for d in side["ducts"]:
                if d["type"] == t and d["zone"] in ("box", "ceil2", "riser") and not d.get("reserve"):
                    o.append(poly(d["pts"], COL[t], d["d"]))
        for s_ in side["shafts"]:
            if s_["kind"] == "node":
                o.append(node_svg(s_))
        for h in side["holes"]:
            if h.get("floor", 2) == 2:
                o.append(hole_svg(h))
        for g in side["grilles"]:
            if not g.get("reserve"):
                o.append(grille_svg(g))
        for e in side["elec"]:
            if e["kind"] in ("sensor", "pult") and not e.get("reserve"):
                mx, my = elec_marker_pos(e)
                o.append(marker(mx, my, e["n"]))
        for s_ in side["shafts"]:
            if s_["kind"] == "node":
                x0, x1, y0, y1 = s_["rect"]
                cx = (x0 + x1) / 2
                if s_["id"] == "А":   # подпись снаружи дома, с выноской
                    left = cx < 14850
                    tx = -1100 if left else 30150
                    o.append(f'<line x1="{mp.sx(x0 if left else x1)}" y1="{mp.sy((y0 + y1) / 2)}" x2="{mp.sx(tx)}" y2="{mp.sy((y0 + y1) / 2)}" stroke="#1c2830" stroke-width="12"/>')
                    o.append(text(tx + (-60 if left else 60), (y0 + y1) / 2 - 70, s_["name"], 210, "#1c2830", "end" if left else "start"))
                else:
                    o.append(text(cx, y0 - 330, s_["name"], 200, "#1c2830"))
    g = {(x["room"], x["type"]): x for x in L["grilles"]}
    o.append(mp.dim_h(200, g[("R", "sup")]["pos"][0], 4855 - 600))
    o.append(mp.dim_h(g[("R", "sup")]["pos"][0], g[("R", "eta")]["pos"][0], 4855 - 600))
    o.append(mp.dim_h(200, g[("D1", "sup")]["pos"][0], 8520 + 700))
    o.append(mp.dim_h(g[("D1", "sup")]["pos"][0], g[("D1", "eta")]["pos"][0], 8520 + 700))
    o.append(mp.dim_v(11400 + 800, g[("D2", "sup")]["pos"][1], 12000))
    o.append(mp.dim_v(11400 + 800, g[("D2", "eta")]["pos"][1], g[("D2", "sup")]["pos"][1]))
    lines = [("Как идут трубы (каждая половина, вторая зеркально):", "#1c2830", 700),
             ("1. Рекуператор во дворе → короб по фасаду вверх до 2-го этажа", "#333", 400),
             ("2. 4 отверстия Ø180 в ряд в стене Г на 2,90 м (○) — трубы входят в дом; ● — гильзы под кабели", "#333", 400),
             ("3. Короб 50×25 см под потолком лестницы, холла и коридора → кладовая (узел А)", "#333", 400),
             ("4. Узел А → родители и детская (крыло); узел Б (с/у) → детская (центр)", "#333", 400),
             ("Спальни: потолок не опускается. В кладовой и с/у потолок 2,45 м.", "#333", 400)]
    o.append(callout(L, lines, []))
    o.append(legend(-1650, [(COL["sup"], "приток", "line"), (COL["eta"], "вытяжка", "line"),
                            ("#cfd6db", "короб под потолком", "line"), ("#111", "○ отверстие в стене под трубу", "dot"),
                            (PURPLE, "● гильза под кабель / электроточка", "dot")]))
    o.append(text(-205, -2350, "Отверстия: Ø180 под трубу Ø160, Ø150 под Ø125. Узлы А и Б — тройники и ирисовые клапаны, доступ через лючок в потолке.",
                  210, "#444", "start", 400, halo=False))
    return svg.replace("</svg>", "\n".join(o) + "\n</svg>")


# ------------------------------------------------------------------ двор
def sheet_yard():
    svg = base(1, "ВЕНТИЛЯЦИЯ — ЗАДНИЙ ДВОР: РЕКУПЕРАТОРЫ И КОРОБ ПО ФАСАДУ", [
        "Рекуператоры — во дворе у стены по оси Г. Трубы поднимаются в утеплённом коробе по фасаду и входят в дом сквозь стену Г на уровне потолка 2-го этажа.",
        "Кровлю не сверлим. Забор — во дворе на 2 м. Выброс — по фасаду снаружи на 1 м выше кровли: забор и выброс разнесены, выброс не засасывается.",
    ], drop_yard=True)
    o = [f"<defs>{DEFS}</defs>"]
    for side in (L, R):
        o.append(unit_svg(side))
        for d in side["ducts"]:
            if d["zone"] in ("riser", "yard"):
                o.append(poly(d["pts"], COL[d["type"]], d["d"]))
        for d in side["ducts"]:
            if d["type"] in ("oda", "eha"):
                x, y = d["pts"][-1][:2]
                o.append(f'<circle cx="{mp.sx(x)}" cy="{mp.sy(y)}" r="190" fill="{COL[d["type"]]}" stroke="#1c2830" stroke-width="20"/>')
        for h in side["holes"]:
            if "Г" in h["wall"]:
                o.append(hole_svg(h))
        u = side["unit"]["rect"]
        o.append(callout(side, yard_lines(side), [((u[0] + u[1]) / 2, u[2])]))
    x0, x1, y0, y1 = L["unit"]["rect"]
    o.append(mp.dim_h(5750, x0, y1 + 350))
    o.append(mp.dim_h(x0, x1, y1 + 350))
    o.append(legend(-1650, [(COL["sup"], "приток", "line"), (COL["eta"], "вытяжка", "line"),
                            (COL["oda"], "забор", "dot"), (COL["eha"], "выброс", "dot"),
                            ("#111", "○ отверстия в стене Г (на уровне 2-го этажа)", "dot")]))
    o.append(text(-205, -2350, "Привязка — от края двери во двор, см; от стены 5 см. Вид на стену со двора — на листе «Фасад и разрез».",
                  210, "#444", "start", 400, halo=False))
    return svg.replace("</svg>", "\n".join(o) + "\n</svg>")


# ------------------------------------------------------------------ 1-й этаж (резерв)
def sheet_floor1():
    svg = base(1, "ВЕНТИЛЯЦИЯ — 1-й ЭТАЖ: РЕЗЕРВ ПОД СПАЛЬНЮ", [
        "Делается, только если центральная комната 1-го этажа станет спальней: трубы опускаются из общего санузла 2-го эт. через две гильзы в перекрытии.",
        "Если не сейчас — оставьте в перекрытии две гильзы Ø180 (Б1, Б2) и заглушите. Приток — 2,90 м, вытяжка — 0,30 м от пола.",
    ], drop_yard=True)
    o = [f"<defs>{DEFS}</defs>"]
    for side in (L, R):
        o.append(unit_svg(side, faded=True))
        for d in side["ducts"]:
            if d["zone"] == "ceil1":
                o.append(poly(d["pts"], COL[d["type"]], d["d"], dash="260 160"))
        for s_ in side["shafts"]:
            if s_["kind"] == "sleeve":
                o.append(shaft_svg(s_, faded=True))
        for g in side["grilles"]:
            if g.get("reserve"):
                o.append(grille_svg(g))
        cx = (side["shafts"][2]["rect"][0] + side["shafts"][2]["rect"][1]) / 2
        tx = cx + (1700 if cx < 14850 else -1700)
        o.append(f'<line x1="{mp.sx(cx)}" y1="{mp.sy(11500)}" x2="{mp.sx(tx)}" y2="{mp.sy(8600)}" stroke="#1c2830" stroke-width="12"/>')
        o.append(text(tx, 8350, "гильзы Б1, Б2 (резерв)", 200, "#1c2830"))
    g = {(x["room"], x["type"]): x for x in L["grilles"]}
    o.append(mp.dim_v(10900 + 420, g[("K1", "sup")]["pos"][1], 12000))
    o.append(mp.dim_v(10900 + 420, g[("K1", "eta")]["pos"][1], g[("K1", "sup")]["pos"][1]))
    o.append(legend(-1650, [(COL["sup"], "приток (резерв)", "dash"), (COL["eta"], "вытяжка (резерв)", "dash"),
                            ("#33414b", "гильза в перекрытии", "shaft")]))
    o.append(text(-205, -2350, "Размеры в см. Во дворе показаны рекуператоры и короб на фасаде (бледно).", 210, "#444", "start", 400, halo=False))
    return svg.replace("</svg>", "\n".join(o) + "\n</svg>")


# ------------------------------------------------------------------ электрика
def sheet_elec():
    fade = f'<rect x="0" y="0" width="{mp.VB[2] - mp.VB[0]}" height="{mp.VB[3] - mp.VB[1]}" fill="#fff" opacity="0.45"/>'
    svg = base(2, "ЭЛЕКТРИКА ДЛЯ ВЕНТИЛЯЦИИ — 2-й ЭТАЖ И ДВОР", drop_yard=True, notes=[
        "Номера точек — как в таблице «Электрика». Правая половина — зеркально, номера те же.",
        "Красное — силовые кабели (во дворе), фиолетовое — витая пара (в тех же коробах и потолках, что и трубы), оранжевое — греющий кабель дренажа.",
    ], pre=fade)
    o = [f"<defs>{DEFS}</defs>"]
    for side in (L, R):
        for b in side["boxes"]:
            o.append(box_svg(b, faded=True))
        for d in side["ducts"]:
            if d["zone"] in ("ceil2", "box", "riser") and d["type"] in ("sup", "eta") and not d.get("reserve"):
                o.append(poly(d["pts"], COL[d["type"]], d["d"], opacity=0.18))
        o.append(unit_svg(side))
        for wi in side["wires"]:
            if not wi.get("reserve"):
                o.append(wire_svg(wi))
        for e in side["elec"]:
            if e.get("reserve") or e["kind"] in ("entry", "isolator", "socket", "heat"):
                continue
            mx, my = elec_marker_pos(e)
            o.append(marker(mx, my, e["n"]))
        u = side["unit"]["rect"]
        lines = [(f"Задний двор ({side['tag']}), у рекуператора:", "#1c2830", 700),
                 ("1 — ввод кабелей через стену Г за лестницей, h 0,3 м", PURPLE, 600),
                 ("2 — выключатель IP65 + питание 5×4, h 1,3 м над агрегатом", "#c0392b", 600),
                 ("3 — розетка IP65 (3×2,5, УЗО 30 мА), h 1,3 м рядом", "#c0392b", 600),
                 ("4 — греющий кабель дренажа → трап во дворе", "#e67e22", 600)]
        o.append(callout(side, lines, [((u[0] + u[1]) / 2, u[2])]))
    o.append(legend(-1650, [("#c0392b", "силовой кабель (линии 1 и 2)", "line"), (PURPLE, "витая пара (пульт, датчики)", "dash"),
                            ("#e67e22", "греющий кабель дренажа", "line"), (PURPLE, "точка — номер в таблице", "dot")]))
    o.append(text(-205, -2350, "Витая пара от пульта и датчиков: по коробу коридора и лестницы → через отверстие в стене Г → короб на фасаде → рекуператор. "
                  "Подрозетники — 1,5 м от пола.", 210, "#444", "start", 400, halo=False))
    return svg.replace("</svg>", "\n".join(o) + "\n</svg>")


# ------------------------------------------------------------------ разрез и спецификация
def section_svg():
    """Схематичный разрез: спальня — с/у (узел) — стена Г — короб на фасаде — рекуператор во дворе. Кровля целая."""
    W, H = 1500, 860
    k = 0.095
    base_y = 800

    def Y(z):
        return base_y - z * k

    c, fl2, roof = vent.C2, vent.FL2, vent.ROOF
    zc, ze = vent.Z_CEIL2, vent.Z_ETA_CEIL2
    g = [f'<svg viewBox="0 0 {W} {H}" font-family="DejaVu Sans, Arial, sans-serif" font-size="21">', f'<defs>{DEFS}</defs>']
    g.append(f'<rect x="20" y="{Y(0)}" width="1460" height="14" fill="#9db083"/>')
    g.append(f'<rect x="40" y="{Y(roof)}" width="1060" height="{Y(c) - Y(roof)}" fill="#b8b2a8"/>')
    g.append(f'<rect x="40" y="{Y(fl2)}" width="1060" height="{Y(fl2 - 250) - Y(fl2)}" fill="#b8b2a8"/>')
    g.append(f'<rect x="1060" y="{Y(roof)}" width="40" height="{Y(0) - Y(roof)}" fill="#3a3a3a"/>')
    g.append(f'<rect x="520" y="{Y(c)}" width="22" height="{Y(fl2) - Y(c)}" fill="#3a3a3a"/>')
    g.append(f'<line x1="542" y1="{Y(fl2 + 2450)}" x2="1060" y2="{Y(fl2 + 2450)}" stroke="#555" stroke-width="3" stroke-dasharray="8 5"/>')
    g.append(f'<text x="800" y="{Y(fl2 + 2450) + 26}" text-anchor="middle" fill="#555" font-size="18">подшивной потолок с/у / кладовой, 2,45 м</text>')
    # короб на фасаде
    g.append(f'<rect x="1100" y="{Y(c + 100)}" width="64" height="{Y(0) - Y(c + 100)}" fill="#e3e7ea" stroke="#33414b" stroke-width="2"/>')
    # приток: рекуператор -> короб -> сквозь стену -> потолок с/у -> решётка
    g.append(f'<polyline points="1215,{Y(500)} 1125,{Y(500)} 1125,{Y(zc)} 542,{Y(zc)} 505,{Y(zc)}" '
             f'fill="none" stroke="{COL["sup"]}" stroke-width="10" stroke-linejoin="round"/>')
    g.append(f'<rect x="500" y="{Y(zc) - 8}" width="20" height="16" fill="{COL["sup"]}" stroke="#1c2830"/>')
    g.append(f'<line x1="495" y1="{Y(zc)}" x2="380" y2="{Y(zc)}" stroke="{COL["sup"]}" stroke-width="4" marker-end="url(#arr-sup)"/>')
    # вытяжка: решётка у пола -> короб в углу с/у -> потолок (2,60) -> сквозь стену -> короб -> рекуператор
    g.append(f'<polyline points="505,{Y(fl2 + 300)} 575,{Y(fl2 + 300)} 575,{Y(ze)} 960,{Y(ze)} 960,{Y(zc - 110)} 1145,{Y(zc - 110)} 1145,{Y(500)} 1215,{Y(500)}" '
             f'fill="none" stroke="{COL["eta"]}" stroke-width="10" stroke-linejoin="round"/>')
    g.append(f'<rect x="500" y="{Y(fl2 + 300) - 8}" width="20" height="16" fill="{COL["eta"]}" stroke="#1c2830"/>')
    g.append(f'<line x1="380" y1="{Y(fl2 + 300)}" x2="495" y2="{Y(fl2 + 300)}" stroke="{COL["eta"]}" stroke-width="4" marker-end="url(#arr-eta)"/>')
    g.append(f'<path d="M380,{Y(zc) + 6} C 120,{Y(zc) + 6} 90,{Y(fl2 + 300) - 6} 360,{Y(fl2 + 300) - 6}" fill="none" stroke="#888" stroke-width="3" stroke-dasharray="8 6" marker-end="url(#arr-eta)"/>')
    # отверстия в стене Г
    g.append(f'<circle cx="1080" cy="{Y(zc) - 2}" r="13" fill="#fff" stroke="#111" stroke-width="3"/>')
    # рекуператор
    u0, u1 = vent.GROUND, vent.GROUND + vent.UNIT_H
    g.append(f'<rect x="1215" y="{Y(u1)}" width="170" height="{Y(u0) - Y(u1)}" fill="#eef1f3" stroke="#1c2830" stroke-width="2"/>')
    g.append(f'<text x="1300" y="{Y((u0 + u1) / 2) + 7}" text-anchor="middle" font-weight="700" font-size="17">рекуператор</text>')
    g.append(f'<polyline points="1260,{Y(u1)} 1260,{Y(2000)}" fill="none" stroke="{COL["oda"]}" stroke-width="13"/>')
    g.append(f'<path d="M1235,{Y(2000) - 22} h50 l-25,22 z" fill="{COL["oda"]}"/>')
    g.append(f'<text x="1290" y="{Y(2000) - 6}" fill="{COL["oda"]}" font-weight="700" font-size="18">забор, 2,0 м</text>')
    g.append(f'<polyline points="1385,{Y(300)} 1420,{Y(300)} 1420,{Y(roof + 1000)}" fill="none" stroke="{COL["eha"]}" stroke-width="13"/>')
    g.append(f'<path d="M1395,{Y(roof + 1000)} h50 l-25,-22 z" fill="{COL["eha"]}"/>')
    g.append(f'<text x="1400" y="{Y(roof + 1000) - 30}" text-anchor="end" fill="{COL["eha"]}" font-weight="700" font-size="18">выброс по фасаду, +1 м над кровлей</text>')

    def mark(z, label, x=50, dy=-8):
        g.append(f'<line x1="{x}" y1="{Y(z)}" x2="{x + 18}" y2="{Y(z)}" stroke="#c0392b" stroke-width="3"/>')
        g.append(f'<text x="{x + 24}" y="{Y(z) + dy}" fill="#c0392b" font-weight="700" font-size="18">{label}</text>')
    mark(fl2, "пол 2-го эт.", 50)
    mark(zc, "2,90 приток", 50, -10)
    mark(fl2 + 300, "0,30 вытяжка", 50, -8)
    g.append(f'<text x="280" y="{Y(fl2 + 1400)}" text-anchor="middle" font-size="19" font-weight="700" fill="#555">СПАЛЬНЯ</text>')
    g.append(f'<text x="280" y="{Y(fl2 + 1400) + 22}" text-anchor="middle" fill="#555" font-size="17">потолок не опускается</text>')
    g.append(f'<text x="800" y="{Y(fl2 + 1300)}" text-anchor="middle" font-size="19" font-weight="700" fill="#555">САНУЗЕЛ / КЛАДОВАЯ</text>')
    g.append(f'<text x="560" y="{Y(1500)}" text-anchor="middle" font-size="19" font-weight="700" fill="#555">1-й ЭТАЖ</text>')
    g.append(f'<text x="800" y="{Y(roof) - 12}" text-anchor="middle" fill="#555" font-size="17">кровля — без отверстий</text>')
    g.append(f'<text x="1040" y="{Y(zc) - 26}" text-anchor="end" fill="#111" font-size="16">4 отверстия в стене Г в ряд, 2,90 м →</text>')
    g.append(f'<text x="770" y="{Y(ze) - 8}" text-anchor="middle" fill="{COL["eta"]}" font-size="15">вытяжка опускается на 2,60</text>')
    g.append(f'<text x="1300" y="{Y(-150) + 30}" text-anchor="middle" fill="#555" font-size="17">ЗАДНИЙ ДВОР</text>')
    g.append("</svg>")
    return "".join(g)


def facade_svg():
    """Вид со двора на стену по оси Г (левая половина): рекуператор, короб, отверстия, выброс над кровлей."""
    x0, x1 = 4300, 14600
    z0, z1 = -600, vent.ROOF + 1500
    k = 0.11
    W, H = (x1 - x0) * k + 120, (z1 - z0) * k + 40

    def X(x):
        return 60 + (x - x0) * k

    def Y(z):
        return 20 + (z1 - z) * k

    roof, fl2, c = vent.ROOF, vent.FL2, vent.C2
    g = [f'<svg viewBox="0 0 {W:.0f} {H:.0f}" font-family="DejaVu Sans, Arial, sans-serif" font-size="20">', f'<defs>{DEFS}</defs>']
    g.append(f'<rect x="{X(4600)}" y="{Y(roof)}" width="{(10495 - 4600) * k}" height="{(roof) * k}" fill="#f1ece4" stroke="#555" stroke-width="2"/>')
    g.append(f'<rect x="{X(4300)}" y="{Y(roof)}" width="{300 * k}" height="{roof * k}" fill="#d8d2c8" stroke="#555" stroke-width="2"/>')
    g.append(f'<rect x="{X(10495)}" y="{Y(2600)}" width="{(11000 - 10495) * k}" height="{2600 * k}" fill="#d8d2c8" stroke="#555" stroke-width="2"/>')
    g.append(f'<line x1="{X(4300)}" y1="{Y(0)}" x2="{X(11000)}" y2="{Y(0)}" stroke="#6c8a4e" stroke-width="5"/>')
    g.append(f'<line x1="{X(4600)}" y1="{Y(fl2)}" x2="{X(10495)}" y2="{Y(fl2)}" stroke="#999" stroke-width="2" stroke-dasharray="10 6"/>')
    g.append(f'<text x="{X(10450)}" y="{Y(fl2) - 6}" text-anchor="end" fill="#888" font-size="17">уровень пола 2-го эт.</text>')
    # проёмы
    g.append(f'<rect x="{X(4850)}" y="{Y(2100)}" width="{900 * k}" height="{2100 * k}" fill="#fff" stroke="#555" stroke-width="2"/>')
    g.append(f'<text x="{X(5300)}" y="{Y(1050)}" text-anchor="middle" fill="#777" font-size="17">дверь</text>')
    for zz in (850, fl2 + 850):
        g.append(f'<rect x="{X(9000)}" y="{Y(zz + 1400)}" width="{750 * k}" height="{1400 * k}" fill="#dceefb" stroke="#3d8fd1" stroke-width="2"/>')
    # рекуператор
    u = L["unit"]["rect"]
    g.append(f'<rect x="{X(u[0])}" y="{Y(vent.GROUND + vent.UNIT_H)}" width="{(u[1] - u[0]) * k}" height="{vent.UNIT_H * k}" fill="#eef1f3" stroke="#1c2830" stroke-width="3"/>')
    g.append(f'<text x="{X((u[0] + u[1]) / 2)}" y="{Y(vent.GROUND + vent.UNIT_H / 2) + 7}" text-anchor="middle" font-weight="700" font-size="18">рекуператор</text>')
    # короб
    r = L["riser"]["rect"]
    g.append(f'<rect x="{X(r[0])}" y="{Y(c + 100)}" width="{(r[1] - r[0]) * k}" height="{(c + 100) * k}" fill="#e3e7ea" stroke="#33414b" stroke-width="2" opacity=".9"/>')
    g.append(f'<text x="{X((r[0] + r[1]) / 2)}" y="{Y(2600)}" text-anchor="middle" fill="#33414b" font-size="17" transform="rotate(-90 {X((r[0] + r[1]) / 2)} {Y(2600)})">короб ~130×50 см</text>')
    # отверстия
    for h in L["holes"]:
        if "Г" in h["wall"]:
            col = PURPLE if h.get("cable") else COL["sup"] if "приток" in h["what"] else COL["eta"]
            g.append(f'<circle cx="{X(h["pos"][0])}" cy="{Y(h["pos"][2])}" r="{max(h["d"] / 2 * k, 4) + 2}" fill="#fff" stroke="{col}" stroke-width="4"/>')
    g.append(f'<text x="{X(10700)}" y="{Y(vent.Z_CEIL2) - 4}" fill="#111" font-size="18">← 4 отверстия Ø180 в ряд, шаг 30 см,</text>')
    g.append(f'<text x="{X(10700)}" y="{Y(vent.Z_CEIL2) + 18}" fill="#111" font-size="18">центр 2,90 м над полом 2-го эт.</text>')
    g.append(f'<text x="{X(10700)}" y="{Y(vent.Z_CEIL2) + 40}" fill="{PURPLE}" font-size="17">● ниже — гильза Ø32 под витую пару</text>')
    g.append(f'<text x="{X(7000)}" y="{Y(-250)}" text-anchor="middle" fill="{PURPLE}" font-size="16">● гильзы Ø50 под силовые кабели, 0,3 м от земли</text>')
    # выброс над кровлей
    g.append(f'<line x1="{X(8550)}" y1="{Y(c + 100)}" x2="{X(8550)}" y2="{Y(roof + 1000)}" stroke="{COL["eha"]}" stroke-width="{250 * k}"/>')
    g.append(f'<path d="M{X(8550) - 22},{Y(roof + 1000)} h44 l-22,-20 z" fill="{COL["eha"]}"/>')
    g.append(f'<text x="{X(8800)}" y="{Y(roof + 800)}" fill="{COL["eha"]}" font-weight="700" font-size="18">выброс: по стене снаружи,</text>')
    g.append(f'<text x="{X(8800)}" y="{Y(roof + 800) + 22}" fill="{COL["eha"]}" font-weight="700" font-size="18">+1 м над кровлей</text>')
    # забор
    g.append(f'<line x1="{X(6300)}" y1="{Y(vent.GROUND + vent.UNIT_H)}" x2="{X(6300)}" y2="{Y(2000)}" stroke="{COL["oda"]}" stroke-width="{250 * k}"/>')
    g.append(f'<path d="M{X(6300) - 22},{Y(2000) - 20} h44 l-22,20 z" fill="{COL["oda"]}"/>')
    g.append(f'<text x="{X(6450)}" y="{Y(2050)}" fill="{COL["oda"]}" font-weight="700" font-size="18">забор, 2,0 м</text>')
    g.append(f'<text x="{X(7000)}" y="{Y(roof) - 10}" text-anchor="middle" fill="#555" font-size="17">кровля — без отверстий</text>')
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
    rows_holes = "".join(
        f'<tr{" class=res" if h.get("cable") else ""}><td>{h["wall"]}</td><td>{h["what"]}</td><td class=n>{h["d"]}</td>'
        f'<td class=n>{str(round((h["pos"][2] - (0 if h.get("floor") == 1 else vent.FL2)) / 1000, 2)).replace(".", ",")} м</td></tr>'
        for h in L["holes"])
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
svg{{display:block;width:100%;height:58mm}}
h2{{margin-top:3.5mm}}
</style></head><body>
<h1>Вентиляция спален: разрез, спецификация, электрика</h1>
<p class="muted">Два рекуператора по 1000 м³/ч в заднем дворе, по одному на каждую половину дома (половины зеркальны). Приточно-вытяжная система только для спален. Все цифры — на ОДНУ половину дома, на весь дом ×2.</p>
<div class="grid">
<div>

<h2>Расходы воздуха (одна половина)</h2>
<table><tr><th>Помещение</th><th>Чел.</th><th>м²</th><th>Приток, м³/ч</th><th>Вытяжка, м³/ч</th><th>Труба</th></tr>
{rows_rooms}
<tr><td><b>Итого на рекуператор</b></td><td></td><td></td><td class=n><b>{L["total"]}</b></td><td class=n><b>{L["total"]}</b></td><td>Ø200 / Ø160</td></tr>
<tr class=res><td>С резервом 1-го этажа</td><td></td><td></td><td class=n>{L["totalWithReserve"]}</td><td class=n>{L["totalWithReserve"]}</td><td></td></tr></table>
<p class="muted">Расчёт: 60 м³/ч на спящего человека (CO₂ ниже ~900 ppm при закрытой двери), не меньше одного обмена в час и не меньше 90 м³/ч на спальню. Скорость в Ø125 — до 2,7 м/с, в Ø160 — до 2,9 м/с (тихо). Рекуператор 1000 м³/ч работает на 33–45% — с большим запасом; по расчёту хватило бы агрегата на 500–600 м³/ч.</p>
<h2>Забор и выброс воздуха</h2>
<ul>
<li><b>Забор и выброс разнесены по высоте.</b> Двор узкий (~2 м до соседей) и закрытый — на одной высоте выброс засасывался бы обратно.</li>
<li><b>Забор</b> — колпак сеткой вниз на высоте 2 м от земли (меньше пыли, чем у земли; в тени двора летом воздух прохладнее, чем над кровлей).</li>
<li><b>Выброс</b> — труба по стене снаружи (на кронштейнах), дефлектор на 1 м выше кровли, в 5–6 м по высоте от забора. Кровлю не сверлим.</li>
<li>Забор не ближе 8 м от дымохода котла (котельная может быть во внутреннем дворике у оси Г), от выхода кухонной вытяжки и не ближе 3 м от фановых стояков (лучше выше них).</li>
<li>Фильтры: приток — F7 (пыль, пыльца), вытяжка — G4/M5. Рекуператор — в уличном исполнении или под навесом/в утеплённом коробе, с электроподогревателем и дренажом в трап.</li>
<li>Рекуператор стоит в заднем дворе у стены по оси Г, на бетонной подушке и виброопорах, в стороне от двери во двор.</li>
</ul>

</div>
<div>
<h2>Решётки: приток вверху (2,90 м), вытяжка внизу (0,30 м)</h2>
<table><tr><th>Спальня</th><th>Стена</th><th>Приток, см от угла</th><th>Вытяжка, см от угла</th><th>Угол отсчёта</th></tr>{rows_grilles}</table>
<p class="muted">Обе решётки на одной стене (трубы приходят из соседнего санузла/кладовой), поэтому их разнесли по высоте: приток вверху дует вдоль потолка до дальней стены, воздух опускается и по полу возвращается к вытяжке внизу — проходит через всю комнату и не уходит сразу в вытяжку. Приток — дальнобойная решётка 200×100 с регулируемыми жалюзи (струя 4–5 м), жалюзи — горизонтально к дальней стене. Вытяжка — решётка 200×100 у пола. Вытяжная труба опускается к ней в коробе ~20×20 см в углу санузла/кладовой. Отверстия в стене — Ø150.</p>
<h2>Отверстия в стенах (на половину дома)</h2>
<table><tr><th>Стена</th><th>Что</th><th>Ø отв.</th><th>Центр от пола этажа</th></tr>{rows_holes}</table>
<h2>Трасса, короба и узлы</h2>
<ul>
<li><b>Кровлю не сверлим.</b> Трубы входят в дом сквозь стену Г со двора: 4 отверстия Ø180 в ряд (шаг 30 см) на 2,90 м над полом 2-го эт.; ниже — гильза Ø32 под витую пару (см. таблицу).</li>
<li><b>Короб на фасаде</b> ~120×40 см, утеплённый: приток и вытяжка Ø200 от рекуператора до отверстий; выброс Ø250 — дальше вверх по стене, над кровлей.</li>
<li><b>Короб под потолком</b> лестницы, холла и коридора ~50×25 см: 2 трубы Ø160 к кладовой. В лестнице — ещё короб 2×Ø160 к общему санузлу.</li>
<li><b>Узел А</b> (кладовая) и <b>узел Б</b> (общий с/у): подшивной потолок 2,45 м, трубы в два яруса (приток 2,90, вытяжка 2,60), тройники и ирисовые клапаны, лючок.</li>
<li>Внутри дома — гибкие гофрированные трубы; лучше полужёсткие с гладкой внутренней стенкой. Каждый отвод — не длиннее 3–4 м, натянут без провисов, поворотов минимум.</li>
<li>На каждом отводе — ирисовый клапан для настройки расхода, доступ через лючок в подшивном потолке санузла или кладовой.</li>
<li>Шумоглушители Ø160 длиной 1 м — в коробе под потолком лестницы сразу после стены Г. Между решётками двух спален — ≥ 1,5 м трубы (меньше «переговоров» между комнатами).</li>
<li>В коробе на фасаде трубы — в утеплителе 50 мм. Отверстия в стене Г после монтажа заделать пеной и герметиком снаружи.</li>
</ul>
</div>
<div>
<h2>Электрика — что оставить (на каждую половину дома)</h2>
<table><tr><th>№</th><th>Что</th><th>Где, высота</th><th>Кабель</th></tr>{rows_elec}</table>
<h2>В щите (на каждый рекуператор)</h2>
<table><tr><th>Линия</th><th>Автомат</th><th>Кабель</th><th>Куда</th></tr>
<tr><td>1. Рекуператор</td><td>по паспорту агрегата (обычно 1P C16–C25 или 3P C16)</td><td>5×4 мм²</td><td>выключатель IP65 на стене над агрегатом (2)</td></tr>
<tr><td>2. Розетка и обогрев дренажа</td><td>дифавтомат 1P C16, 30 мА</td><td>3×2,5 мм²</td><td>розетка IP65 (3) и коробка греющего кабеля (4)</td></tr></table>
<p class="muted">В каждой шахте — ещё пустая гофра Ø32 с протяжкой на запас. Слаботочные кабели ведите отдельно от силовых (не в одной гофре). Точное сечение и номинал автомата — по паспорту выбранной модели. Без электроподогревателя агрегату хватает 3×2,5 мм², но в Ташкенте зимой бывает −10…−15 °C, и пластинчатый рекуператор без подогрева обмерзает — поэтому кабель с запасом.</p>
<h2>Чего эта схема не делает</h2>
<ul><li>Санузлы и кухня вентилируются отдельно (свои вытяжные вентиляторы и трубы на кровлю); их выходы — не ближе 3 м от забора рекуператора.</li></ul></div></div></body></html>"""


def facade_html():
    return f"""<!doctype html><html lang="ru"><head><meta charset="utf-8"><title>Фасад и разрез</title>
<style>@page{{size:A3 landscape;margin:12mm}}
body{{font-family:"DejaVu Sans",Arial,sans-serif;color:#1c2830;margin:0;font-size:10pt}}
h1{{font-size:20pt;margin:0 0 2mm}} h2{{font-size:12.5pt;margin:3mm 0 2mm;text-transform:uppercase;letter-spacing:.04em;color:#444}}
.grid{{display:grid;grid-template-columns:1fr 1fr;gap:10mm;align-items:start}} svg{{display:block;width:100%;height:auto;max-height:235mm}}
p{{color:#555;margin:0 0 2mm}}</style></head><body>
<h1>Как трубы попадают в дом: фасад со двора и разрез</h1>
<p>Кровлю не сверлим. От рекуператора во дворе трубы поднимаются в коробе по стене Г, входят в дом через 4 отверстия на уровне потолка 2-го этажа и дальше идут в коробах под потолком лестницы/холла/коридора и в подшивных потолках кладовой и санузла. Левая половина; правая зеркальна.</p>
<div class="grid"><div><h2>Фасад по оси Г, вид со двора</h2>{facade_svg()}</div>
<div><h2>Разрез: спальня — санузел — стена Г — двор</h2>{section_svg()}</div></div></body></html>"""


if __name__ == "__main__":
    os.makedirs(mp.OUT, exist_ok=True)
    for name, fn in (("vent-1-etazh-2.svg", sheet_floor2), ("vent-2-krovlya.svg", sheet_yard),
                     ("vent-3-etazh-1.svg", sheet_floor1), ("vent-5-elektrika.svg", sheet_elec)):
        with open(os.path.join(mp.OUT, name), "w", encoding="utf-8") as fh:
            fh.write(fn())
        print("ok", name)
    with open(os.path.join(mp.OUT, "vent-4-spec.html"), "w", encoding="utf-8") as fh:
        fh.write(spec_html())
    with open(os.path.join(mp.OUT, "vent-6-fasad.html"), "w", encoding="utf-8") as fh:
        fh.write(facade_html())
    print("ok spec")

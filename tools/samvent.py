"""Вентиляция спален по схеме «СамВент»: приток через стеновые клапаны, вытяжка вентилятором.

Как работает (каждая половина дома, вторая — зеркально):
  1. Свежий воздух входит в спальни через приточные клапаны в наружных стенах (без электричества).
  2. Из спальни идёт под дверью (щель 2 см) в коридор / санузел.
  3. Вентилятор вытягивает воздух из санузла у родителей, кладовой и общего санузла по гибким
     трубам Ø90 через коллектор и выбрасывает во двор сквозь заднюю стену (ось Г). Кровлю не сверлим.

Координаты — мм в системе осей чертежа (ось 1 = X 0, ось А = Y 0), Z — от пола 1-го этажа.
Правая половина: крыло и лестница — зеркало по X = 14850, центр — по оси 5 (X = 14600).
Используется в export_model.py (3D-приложение) и make_samvent.py (чертёж).
"""
import math

import make_plan as mp

FL2 = 3300
C2 = FL2 + 3050                # потолок 2-го этажа
ROOF = C2 + 250
Z_DUCT = C2 - 100              # гибкие трубы под потолком (короб ~10 см)
Z_FALSE = FL2 + 2450           # подшивной потолок санузлов и кладовой — там стоят вытяжные решётки
Z_VALVE = FL2 + 2100           # приточный клапан: 2,1 м от пола
Z_VALVE_HIGH = FL2 + 2650      # над окном
PIPE = 90                      # гибкая антибактериальная труба Ø90
PIPE_FLOW = 45                 # м³/ч на одну трубу Ø90 (тихо)
VALVE_FLOW = 60                # м³/ч на один стеновой клапан Ø125 при разрежении ~10 Па

WING_AXIS, CENTER_AXIS, PART_X = 29700, 29200, 8620

ROOMS = [
    # id, название, людей, площадь, расход м³/ч (60 на человека, не меньше 90)
    ("R", "Комната (родители)", 2, 18.6, 120),
    ("D1", "Детская (крыло)", 1, 20.0, 90),
    ("D2", "Детская (центр)", 2, 15.4, 120),
]


def offset_path(pts, o):
    """Сдвиг ортогональной ломаной на o мм влево по ходу (для пучка параллельных труб)."""
    def nrm(a, b):
        dx, dy = b[0] - a[0], b[1] - a[1]
        L = math.hypot(dx, dy) or 1
        return -dy / L, dx / L
    out = []
    for i, p in enumerate(pts):
        n1 = nrm(pts[i - 1], p) if i > 0 else None
        n2 = nrm(p, pts[i + 1]) if i < len(pts) - 1 else None
        if n1 and n2:
            nx, ny = n1[0] + n2[0], n1[1] + n2[1]
            if abs(n1[0] - n2[0]) < 1e-6 and abs(n1[1] - n2[1]) < 1e-6:
                nx, ny = n1
        else:
            nx, ny = n1 or n2
        out.append([round(p[0] + nx * o), round(p[1] + ny * o)] + list(p[2:]))
    return out


def left_side():
    rooms = {r: {"id": r, "name": n, "people": p, "area": a, "flow": q, "reserve": False}
             for r, n, p, a, q in ROOMS}
    # --- приточные клапаны в наружных стенах спален: pos — грань стены со стороны комнаты, n — внутрь
    valves = [
        {"room": "R", "pos": [700, 200, Z_VALVE], "n": [0, 1], "hole": [700, 0],
         "wall": "наружная стена с окном", "from": "угол у оси 1", "off": 500},
        {"room": "R", "pos": [3700, 200, Z_VALVE], "n": [0, 1], "hole": [3700, 0],
         "wall": "наружная стена с окном", "from": "угол у оси 2", "off": 500},
        {"room": "D1", "pos": [4200, 12650, Z_VALVE_HIGH], "n": [-1, 0], "hole": [4400, 12650],
         "wall": "стена с окном во двор, над окном", "from": "над окном", "off": 0},
        {"room": "D1", "pos": [4200, 13150, Z_VALVE_HIGH], "n": [-1, 0], "hole": [4400, 13150],
         "wall": "стена с окном во двор, над окном", "from": "над окном", "off": 0},
        {"room": "D2", "pos": [14075, 7000, Z_VALVE], "n": [0, 1], "hole": [14075, 6800],
         "wall": "стена с окном (сторона двора)", "from": "угол у оси 5", "off": 400},
        {"room": "D2", "pos": [14075, 12000, Z_VALVE], "n": [0, -1], "hole": [14075, 12200],
         "wall": "стена с окном (задний двор)", "from": "угол у оси 5", "off": 400},
    ]
    # --- вытяжные решётки в подшивном потолке (2,45 м) и пучки гибких труб Ø90 до коллектора
    fan = {"rect": [7250, 8350, 11450, 11950], "z": [C2 - 400, C2],
           "where": "под потолком лестницы, в углу у задней стены"}
    exhausts = [
        {"id": "В1", "name": "Санузел у родителей", "pos": [1540, 5900], "flow": 120, "pipes": 3, "air_from": "R",
         "path": [[1540, 5900], [1540, 7400], [4900, 7400], [4900, 11700], [7250, 11700]], "offs": [-200, -100, 0]},
        {"id": "В2", "name": "Кладовая", "pos": [2200, 7900], "flow": 90, "pipes": 2, "air_from": "D1",
         "path": [[2200, 7900], [2200, 7400], [4900, 7400], [4900, 11700], [7250, 11700]], "offs": [100, 200]},
        {"id": "В3", "name": "Общий санузел", "pos": [9950, 10800], "flow": 120, "pipes": 3, "air_from": "D2",
         "path": [[9950, 10800], [9950, 11700], [8350, 11700]], "offs": [-100, 0, 100]},
    ]
    outlet = [[7800, 11950], [7800, 12650]]          # Ø160 сквозь стену Г во двор
    # щели под дверями (воздух идёт из спальни к вытяжке)
    doors = [
        {"pos": [2330, 4915], "label": "щель 2 см", "dir": "h"},     # родители → их санузел
        {"pos": [3650, 4915], "label": "щель 2 см", "dir": "h"},     # родители → коридор
        {"pos": [3650, 8460], "label": "щель 2 см", "dir": "h"},     # детская (крыло) → коридор
        {"pos": [2940, 7615], "label": "щель 2 см", "dir": "v"},     # коридор → кладовая
        {"pos": [11275, 7700], "label": "щель 2 см", "dir": "v"},    # детская (центр) → холл
        {"pos": [9950, 9240], "label": "щель 2 см", "dir": "h"},     # холл → общий санузел
    ]
    # путь воздуха (стрелки на чертеже)
    flows = [
        [[2200, 1600], [2330, 4300], [2330, 5500]],
        [[2600, 12300], [3650, 9300], [3650, 7300], [2600, 7700]],
        [[13300, 11100], [12200, 8300], [10600, 7700], [9950, 9800]],
    ]
    elec = [
        {"n": 1, "kind": "fan_power", "pos": [7800, 11400, C2 - 250], "name": "Питание вентилятора",
         "where": "коробка у вентилятора, под потолком лестницы", "h": "3,0 м",
         "cable": "ВВГнг 3×1,5 мм² через регулятор (2)", "route": "регулятор → по стене вверх → под потолком к вентилятору"},
        {"n": 2, "kind": "regulator", "pos": [7300, 7000, FL2 + 1500], "nrm": [0, 1], "name": "Регулятор скорости вентилятора",
         "where": "холл 2-го эт., на стене у окна", "h": "1,5 м от пола",
         "cable": "ВВГнг 3×1,5 мм² от щита (автомат 10 А)", "route": "щит → регулятор"},
    ]
    wires = [
        {"kind": "power", "pts": [[7300, 7000, FL2 + 1500], [7300, 7000, C2 - 60], [7300, 11400, C2 - 60],
                                   [7800, 11400, C2 - 60], [7800, 11400, C2 - 250]]},
        {"kind": "power", "pts": [[7300, 7000, FL2 + 1500], [7300, 7000, FL2 + 150]]},
    ]
    return rooms, valves, fan, exhausts, outlet, doors, flows, elec, wires


def wall_rects():
    for lst in (mp.EXT, mp.PART, mp.COL, mp.WIN, mp.OPEN, mp.ROOMS, mp.EXTRA, mp.GAPS):
        lst.clear()
    mp.floor2()
    return [list(r) for r in mp.EXT + mp.PART + mp.COL + mp.GAPS]


def crossings(pts, walls):
    """Точки, где горизонтальный (в плане) отрезок трубы проходит сквозь стену."""
    out = []
    for a, b in zip(pts, pts[1:]):
        if a[2] != b[2]:
            continue
        for r in walls:
            if a[1] == b[1] and r[2] < a[1] < r[3]:
                lo, hi = sorted((a[0], b[0]))
                if lo < r[0] and hi > r[1] and r[1] - r[0] < 500:
                    out.append([(r[0] + r[1]) / 2, a[1], a[2]])
            if a[0] == b[0] and r[0] < a[0] < r[1]:
                lo, hi = sorted((a[1], b[1]))
                if lo < r[2] and hi > r[3] and r[3] - r[2] < 500:
                    out.append([a[0], (r[2] + r[3]) / 2, a[2]])
    return out


def side(sign):
    rooms, valves, fan, exhausts, outlet, doors, flows, elec, wires = left_side()
    walls = wall_rects()
    tag = "Л" if sign == "L" else "П"
    ducts, grilles, holes = [], [], []
    for v in valves:
        grilles.append({"room": v["room"], "type": "sup", "kind": "valve", "pos": v["pos"], "n": v["n"],
                        "flow": VALVE_FLOW, "wall": v["wall"], "from": v["from"], "off": v["off"]})
        holes.append({"pos": v["hole"] + [v["pos"][2]], "d": 130, "wall": v["wall"], "what": "приточный клапан Ø125"})
    for e in exhausts:
        grilles.append({"room": e["air_from"], "type": "eta", "kind": "ceiling", "pos": e["pos"] + [Z_FALSE], "n": [0, 0],
                        "flow": e["flow"], "id": e["id"], "where": e["name"],
                        "wall": f"подшивной потолок: {e['name'].lower()}", "from": "", "off": 0})
        for o in e["offs"]:
            p = [pt + [Z_DUCT] for pt in offset_path(e["path"], o)]
            p = [[p[0][0], p[0][1], Z_FALSE]] + p
            ducts.append({"type": "eta", "d": PIPE, "zone": "flex", "room": e["air_from"], "exhaust": e["id"],
                          "flow": round(e["flow"] / e["pipes"]), "pts": p})
            for c in crossings(p, walls):
                holes.append({"pos": c, "d": PIPE + 20, "wall": "перегородка", "what": f"труба Ø90 ({e['id']})"})
    ducts.append({"type": "eha", "d": 160, "zone": "outlet", "flow": sum(r["flow"] for r in rooms.values()),
                  "pts": [outlet[0] + [C2 - 200], outlet[1] + [C2 - 200]]})
    holes.append({"pos": [7800, 12200, C2 - 200], "d": 180, "wall": "задняя стена (ось Г)", "what": "выброс Ø160 во двор"})

    def mp_(p):
        if sign == "L":
            return list(p)
        ax = WING_AXIS if p[0] < PART_X else CENTER_AXIS
        return [ax - p[0]] + list(p[1:])

    def mr(r):
        if sign == "L":
            return list(r)
        ax = WING_AXIS if (r[0] + r[1]) / 2 < PART_X else CENTER_AXIS
        return [ax - r[1], ax - r[0], r[2], r[3]]

    flip = (lambda n: [-n[0], n[1]]) if sign == "R" else (lambda n: list(n))
    total = sum(r["flow"] for r in rooms.values())
    for d in ducts:
        d["v"] = round(d["flow"] / 3600 / (math.pi * (d["d"] / 2000) ** 2), 1)
    return {
        "side": sign, "tag": tag, "rooms": list(rooms.values()), "total": total, "totalWithReserve": total,
        "unit": {"rect": mr(fan["rect"]), "z": fan["z"], "name": f"Вентилятор {tag}", "where": fan["where"]},
        "shafts": [],
        "ducts": [dict(d, pts=[mp_(p) for p in d["pts"]]) for d in ducts],
        "grilles": [dict(g, pos=mp_(g["pos"]), n=flip(g["n"])) for g in grilles],
        "holes": [dict(h, pos=mp_(h["pos"])) for h in holes],
        "exhausts": [dict(e, pos=mp_(e["pos"]), path=[mp_(p) for p in e["path"]]) for e in exhausts],
        "doors": [dict(dd, pos=mp_(dd["pos"])) for dd in doors],
        "flows": [[mp_(p) for p in f] for f in flows],
        "elec": [dict(e, pos=mp_(e["pos"]), nrm=flip(e["nrm"]) if e.get("nrm") else None) for e in elec],
        "wires": [dict(w, pts=[mp_(p) for p in w["pts"]]) for w in wires],
        "outlet": [mp_(p) for p in outlet],
    }


def data():
    return {
        "system": "samvent",
        "unitCapacity": 400,
        "levels": {"fl2": FL2, "ceiling2": C2, "roof": ROOF, "duct2": Z_DUCT, "duct1": 2900, "ground": 100},
        "sides": [side("L"), side("R")],
    }


if __name__ == "__main__":
    d = data()
    for s in d["sides"]:
        print(s["tag"], "итого", s["total"], "м³/ч; труб", len([x for x in s["ducts"] if x["zone"] == "flex"]),
              "; отверстий", len(s["holes"]))
        for h in s["holes"]:
            print("   ", h["what"], h["pos"])

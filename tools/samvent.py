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
C1 = 3050                      # потолок 1-го этажа
Z_DUCT1 = C1 - 100
Z_FALSE1 = 2450
Z_VALVE1, Z_VALVE_HIGH1 = 2100, 2650
PIPE = 90                      # гибкая антибактериальная труба Ø90
PIPE_FLOW = 45                 # м³/ч на одну трубу Ø90 (тихо)
VALVE_FLOW = 60                # м³/ч на один стеновой клапан Ø125 при разрежении ~10 Па

WING_AXIS, CENTER_AXIS, PART_X = 29700, 29200, 8620

ROOMS = [
    # id, название, людей, площадь, расход м³/ч (60 на человека, не меньше 90; гостиная — 1 обмен/ч), этаж
    ("R", "Родители", 2, 18.6, 120, 2),
    ("D1", "Детская (крыло)", 1, 20.0, 90, 2),
    ("D2", "Детская (центр)", 2, 15.4, 120, 2),
    ("G1", "Гостиная (крыло)", 3, 52.8, 160, 1),
    ("K1", "Комната (центр)", 2, 17.9, 120, 1),
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
    rooms = {r: {"id": r, "name": n, "people": p, "area": a, "flow": q, "floor": f, "reserve": False}
             for r, n, p, a, q, f in ROOMS}
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
    for x in valves + exhausts + doors + elec + wires:
        x.setdefault("floor", 2)
    fan["floor"] = 2
    flows = [{"floor": 2, "pts": f} for f in flows]
    outlets = [{"floor": 2, "pts": outlet, "z": C2 - 200}]
    fans = [fan]
    # ---------------- 1-й этаж: гостиная в крыле и центральная комната
    valves += [
        {"floor": 1, "room": "G1", "pos": [700, 200, Z_VALVE1], "n": [0, 1], "hole": [700, 0],
         "wall": "наружная стена с окном", "from": "угол у оси 1", "off": 500},
        {"floor": 1, "room": "G1", "pos": [3700, 200, Z_VALVE1], "n": [0, 1], "hole": [3700, 0],
         "wall": "наружная стена с окном", "from": "угол у оси 2", "off": 500},
        {"floor": 1, "room": "G1", "pos": [4200, 12900, Z_VALVE_HIGH1], "n": [-1, 0], "hole": [4400, 12900],
         "wall": "стена с окном во двор, над окном", "from": "над окном", "off": 0},
        {"floor": 1, "room": "K1", "pos": [14075, 7000, Z_VALVE1], "n": [0, 1], "hole": [14075, 6800],
         "wall": "стена с окном (сторона двора)", "from": "угол у оси 5", "off": 400},
        {"floor": 1, "room": "K1", "pos": [14075, 12000, Z_VALVE1], "n": [0, -1], "hole": [14075, 12200],
         "wall": "стена с окном (задний двор)", "from": "угол у оси 5", "off": 400},
    ]
    fans.append({"floor": 1, "rect": [9050, 10450, 11300, 11850], "z": [C1 - 400, C1],
                 "where": "в подшивном потолке ванной 1-го эт., у задней стены"})
    exhausts += [
        {"floor": 1, "id": "В4", "name": "Ванная 1-го эт.", "pos": [9300, 10600], "flow": 160, "pipes": 4, "air_from": "G1",
         "path": [[9300, 10600], [9300, 11300]], "offs": [-150, -50, 50, 150]},
        {"floor": 1, "id": "В5", "name": "Санузел 1-го эт.", "pos": [10000, 9560], "flow": 120, "pipes": 3, "air_from": "K1",
         "path": [[10000, 9560], [10000, 11300]], "offs": [-100, 0, 100]},
    ]
    outlets.append({"floor": 1, "pts": [[10250, 11850], [10250, 12650]], "z": C1 - 200})
    doors += [
        {"floor": 1, "pos": [9800, 8925], "label": "щель 2 см", "dir": "h"},     # холл → санузел
        {"floor": 1, "pos": [10770, 7700], "label": "щель 2 см", "dir": "v"},    # комната → холл
    ]
    flows += [
        {"floor": 1, "pts": [[2200, 2500], [2600, 7000], [6200, 7600], [9300, 8300], [9800, 9300]]},
        {"floor": 1, "pts": [[13000, 10600], [12000, 7700], [10500, 7700], [9900, 8500]]},
    ]
    elec += [
        {"floor": 1, "n": 3, "kind": "fan_power", "pos": [9050, 11550, C1 - 250], "name": "Питание вентилятора 1-го эт.",
         "where": "коробка у вентилятора, в потолке ванной", "h": "2,8 м",
         "cable": "ВВГнг 3×1,5 мм² через регулятор (4)", "route": "регулятор → вверх → в потолке к вентилятору"},
        {"floor": 1, "n": 4, "kind": "regulator", "pos": [9000, 8800, 1500], "nrm": [0, -1],
         "name": "Регулятор скорости 1-го эт.", "where": "холл 1-го эт., у двери санузла", "h": "1,5 м от пола",
         "cable": "ВВГнг 3×1,5 мм² от щита (автомат 10 А)", "route": "щит → регулятор"},
    ]
    wires += [
        {"floor": 1, "kind": "power", "pts": [[9000, 8800, 1500], [9000, 8800, C1 - 60], [9000, 11550, C1 - 60],
                                               [9050, 11550, C1 - 60], [9050, 11550, C1 - 250]]},
        {"floor": 1, "kind": "power", "pts": [[9000, 8800, 1500], [9000, 8800, 150]]},
    ]
    return rooms, valves, fans, exhausts, outlets, doors, flows, elec, wires


def wall_rects(floor=2):
    for lst in (mp.EXT, mp.PART, mp.COL, mp.WIN, mp.OPEN, mp.ROOMS, mp.EXTRA, mp.GAPS):
        lst.clear()
    (mp.floor1 if floor == 1 else mp.floor2)()
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
    rooms, valves, fans, exhausts, outlets, doors, flows, elec, wires = left_side()
    walls = {1: wall_rects(1), 2: wall_rects(2)}
    tag = "Л" if sign == "L" else "П"
    zd = {1: Z_DUCT1, 2: Z_DUCT}
    zf = {1: Z_FALSE1, 2: Z_FALSE}
    ducts, grilles, holes = [], [], []
    for v in valves:
        grilles.append({"floor": v["floor"], "room": v["room"], "type": "sup", "kind": "valve", "pos": v["pos"], "n": v["n"],
                        "flow": VALVE_FLOW, "wall": v["wall"], "from": v["from"], "off": v["off"]})
        holes.append({"pos": v["hole"] + [v["pos"][2]], "d": 130, "wall": v["wall"], "what": "приточный клапан Ø125"})
    for e in exhausts:
        f = e["floor"]
        grilles.append({"floor": f, "room": e["air_from"], "type": "eta", "kind": "ceiling", "pos": e["pos"] + [zf[f]], "n": [0, 0],
                        "flow": e["flow"], "id": e["id"], "where": e["name"],
                        "wall": f"подшивной потолок: {e['name'].lower()}", "from": "", "off": 0})
        for o in e["offs"]:
            p = [pt + [zd[f]] for pt in offset_path(e["path"], o)]
            p = [[p[0][0], p[0][1], zf[f]]] + p
            ducts.append({"floor": f, "type": "eta", "d": PIPE, "zone": "flex", "room": e["air_from"], "exhaust": e["id"],
                          "flow": round(e["flow"] / e["pipes"]), "pts": p})
            for c in crossings(p, walls[f]):
                holes.append({"pos": c, "d": PIPE + 20, "wall": "перегородка", "what": f"труба Ø90 ({e['id']})"})
    for ol in outlets:
        f = ol["floor"]
        q = sum(e["flow"] for e in exhausts if e["floor"] == f)
        ducts.append({"floor": f, "type": "eha", "d": 160, "zone": "outlet", "flow": q,
                      "pts": [ol["pts"][0] + [ol["z"]], ol["pts"][1] + [ol["z"]]]})
        holes.append({"pos": [ol["pts"][0][0], 12200, ol["z"]], "d": 180, "wall": "задняя стена (ось Г)",
                      "what": f"выброс Ø160 во двор ({f}-й эт.)"})

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
    for d in ducts:
        d["v"] = round(d["flow"] / 3600 / (math.pi * (d["d"] / 2000) ** 2), 1)
    units = []
    for fn in fans:
        q = sum(e["flow"] for e in exhausts if e["floor"] == fn["floor"])
        units.append({"floor": fn["floor"], "rect": mr(fn["rect"]), "z": fn["z"], "flow": q,
                      "name": f"Вентилятор {tag}{'' if fn['floor'] == 2 else ' (1 эт.)'}", "where": fn["where"]})
    total = sum(r["flow"] for r in rooms.values())
    return {
        "side": sign, "tag": tag, "rooms": list(rooms.values()), "total": total, "totalWithReserve": total,
        "unit": units[0], "units": units, "shafts": [],
        "ducts": [dict(d, pts=[mp_(p) for p in d["pts"]]) for d in ducts],
        "grilles": [dict(g, pos=mp_(g["pos"]), n=flip(g["n"])) for g in grilles],
        "holes": [dict(h, pos=mp_(h["pos"])) for h in holes],
        "exhausts": [dict(e, pos=mp_(e["pos"]), path=[mp_(p) for p in e["path"]]) for e in exhausts],
        "doors": [dict(dd, pos=mp_(dd["pos"])) for dd in doors],
        "flows": [dict(f, pts=[mp_(p) for p in f["pts"]]) for f in flows],
        "elec": [dict(e, pos=mp_(e["pos"]), nrm=flip(e["nrm"]) if e.get("nrm") else None) for e in elec],
        "wires": [dict(w, pts=[mp_(p) for p in w["pts"]]) for w in wires],
        "outlets": [dict(o, pts=[mp_(p) for p in o["pts"]]) for o in outlets],
    }


def pipe_length(d):
    """Длина гибких труб Ø90 на весь дом, м (с запасом 15 %)."""
    L = 0
    for s in d["sides"]:
        for du in s["ducts"]:
            if du["zone"] == "flex":
                for a, b in zip(du["pts"], du["pts"][1:]):
                    L += abs(a[0] - b[0]) + abs(a[1] - b[1]) + abs(a[2] - b[2])
    return round(L / 1000 * 1.15)


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
        print(s["tag"], "итого", s["total"], [(u["name"], u["flow"]) for u in s["units"]],
              "труб", len([x for x in s["ducts"] if x["zone"] == "flex"]), "отверстий", len(s["holes"]))
        for h in s["holes"]:
            print("   ", h["what"], h["pos"])
    print("гибкой трубы Ø90 на дом, м:", pipe_length(d))

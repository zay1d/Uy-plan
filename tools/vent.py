"""Приточно-вытяжная вентиляция спален: два рекуператора на кровле (по одному на половину дома).

Все координаты в мм в системе осей чертежа (ось 1 = X 0, ось А = Y 0), Z — от пола 1-го этажа.
Левая половина задаётся явно, правая получается зеркалом:
  крыло и лестница — зеркало относительно X = 14850 (середина между осями 1 и 9);
  центральные комнаты и их санузлы — зеркало относительно оси 5 (X = 14600).

Используется в export_model.py (3D-приложение) и make_vent.py (чертежи).
"""
import math

FL2 = 3300            # отметка пола 2-го этажа
C2 = FL2 + 3050       # низ перекрытия над 2-м этажом (потолок спален)
ROOF = C2 + 250       # верх кровли
Z_CEIL2 = C2 - 150    # ось воздуховодов в подшивном потолке с/у и кладовок 2-го этажа
Z_GRILLE2 = C2 - 150  # центр решёток в стенах спален (верх решётки ~10 см от потолка)
Z_CEIL1 = 3050 - 150  # то же для 1-го этажа (резерв)
Z_ROOFDUCT = ROOF + 250   # ось воздуховодов на кровле (на опорах)
UNIT_H = 600

WING_AXIS = 29700      # x' = WING_AXIS - x
CENTER_AXIS = 29200    # x' = CENTER_AXIS - x

# расходы, м³/ч: 60 м³/ч на спящего человека, не меньше 1 обмена в час и не меньше 90 м³/ч на спальню
ROOMS_L = [
    # id, название, этаж, людей, площадь м², объём м³, расход
    ("R", "Комната (родители)", 2, 2, 18.6),
    ("D1", "Детская (крыло)", 2, 1, 20.0),
    ("D2", "Детская (центр)", 2, 2, 15.4),
    ("K1", "Комната 1-го этажа (резерв)", 1, 2, 17.9),
]
HEIGHT = 3.05


def flow(people, area):
    return int(math.ceil(max(60 * people, area * HEIGHT, 90) / 10) * 10)


def mirror_x(pt, axis):
    return [axis - pt[0]] + list(pt[1:])


def mirror_rect(r, axis):
    return [axis - r[1], axis - r[0], r[2], r[3]]


def left_side():
    """Описание левой половины дома."""
    W, C = "wing", "center"
    rooms = {rid: {"id": rid, "name": n, "floor": f, "people": p, "area": a, "flow": flow(p, a),
                   "reserve": rid == "K1"} for rid, n, f, p, a in ROOMS_L}
    unit = {"rect": [4900, 6300, 8700, 9700], "z": [ROOF + 150, ROOF + 150 + UNIT_H], "part": W,
            "label": "Рекуператор"}
    shafts = [
        {"id": "А", "rect": [220, 620, 7020, 7320], "z": [Z_CEIL2 - 150, ROOF], "part": W,
         "where": "кладовая 2-го эт., угол у наружной стены"},
        {"id": "Б", "rect": [10345, 10645, 10300, 10800], "z": [Z_CEIL2 - 150, ROOF], "part": C,
         "where": "с/у общий 2-го эт., у стены детской"},
        {"id": "Б", "rect": [10345, 10645, 10300, 10800], "z": [Z_CEIL1 - 150, FL2], "part": C,
         "where": "продолжение до потолка с/у 1-го эт.", "reserve": True},
    ]
    zc, zr, z1 = Z_CEIL2, Z_ROOFDUCT, Z_CEIL1
    ducts = [
        # --- кровля: агрегат -> шахта А (крыло)
        {"type": "sup", "d": 160, "zone": "roof", "part": W, "to": "А",
         "pts": [[4900, 9050, zr], [4750, 9050, zr], [4750, 7100, zr], [340, 7100, zr], [340, 7100, zc]]},
        {"type": "eta", "d": 160, "zone": "roof", "part": W, "to": "А",
         "pts": [[4900, 9350, zr], [4550, 9350, zr], [4550, 7240, zr], [500, 7240, zr], [500, 7240, zc]]},
        # --- кровля: агрегат -> шахта Б (центр)
        {"type": "sup", "d": 160, "zone": "roof", "part": C, "to": "Б",
         "pts": [[6300, 9350, zr], [10420, 9350, zr], [10420, 10550, zr], [10420, 10550, zc]]},
        {"type": "eta", "d": 160, "zone": "roof", "part": C, "to": "Б",
         "pts": [[6300, 9050, zr], [10570, 9050, zr], [10570, 10550, zr], [10570, 10550, zc]]},
        # --- потолок кладовой / с/у крыла (шахта А)
        {"type": "sup", "d": 125, "zone": "ceil2", "part": W, "room": "D1",
         "pts": [[340, 7100, zc], [340, 8100, zc], [600, 8100, zc], [600, 8520, zc]]},
        {"type": "eta", "d": 125, "zone": "ceil2", "part": W, "room": "D1",
         "pts": [[500, 7240, zc], [500, 7600, zc], [2500, 7600, zc], [2500, 8520, zc]]},
        {"type": "sup", "d": 125, "zone": "ceil2", "part": W, "room": "R",
         "pts": [[340, 7100, zc], [340, 5300, zc], [550, 5300, zc], [550, 4855, zc]]},
        {"type": "eta", "d": 125, "zone": "ceil2", "part": W, "room": "R",
         "pts": [[500, 7240, zc], [500, 6700, zc], [1550, 6700, zc], [1550, 4855, zc]]},
        # --- потолок общего с/у (шахта Б)
        {"type": "sup", "d": 125, "zone": "ceil2", "part": C, "room": "D2",
         "pts": [[10420, 10550, zc], [10420, 11650, zc], [11400, 11650, zc]]},
        {"type": "eta", "d": 125, "zone": "ceil2", "part": C, "room": "D2",
         "pts": [[10570, 10550, zc], [10570, 9700, zc], [11400, 9700, zc]]},
        # --- резерв: комната 1-го этажа (шахта Б вниз до потолка с/у 1-го этажа)
        {"type": "sup", "d": 125, "zone": "ceil1", "part": C, "room": "K1", "reserve": True,
         "pts": [[10420, 10550, zc], [10420, 10550, z1], [10420, 11650, z1], [10900, 11650, z1]]},
        {"type": "eta", "d": 125, "zone": "ceil1", "part": C, "room": "K1", "reserve": True,
         "pts": [[10570, 10550, zc], [10570, 10550, z1], [10570, 9700, z1], [10900, 9700, z1]]},
        # --- наружный воздух и выброс у агрегата (короткие, утеплённые)
        {"type": "oda", "d": 250, "zone": "roof", "part": W,
         "pts": [[5300, 8700, ROOF + 450], [5300, 8000, ROOF + 450], [5300, 8000, ROOF + 900]]},
        {"type": "eha", "d": 250, "zone": "roof", "part": W,
         "pts": [[5900, 9700, ROOF + 450], [5900, 11900, ROOF + 450], [5900, 11900, ROOF + 1900]]},
    ]
    # решётки: стена спальни, центр решётки, нормаль внутрь комнаты
    grilles = [
        {"room": "R", "type": "sup", "pos": [550, 4855, Z_GRILLE2], "n": [0, -1], "part": W,
         "wall": "стена с санузлом", "from": "угол у наружной стены (ось 1)", "off": 350},
        {"room": "R", "type": "eta", "pos": [1550, 4855, Z_GRILLE2], "n": [0, -1], "part": W,
         "wall": "стена с санузлом", "from": "угол у наружной стены (ось 1)", "off": 1350},
        {"room": "D1", "type": "sup", "pos": [600, 8520, Z_GRILLE2], "n": [0, 1], "part": W,
         "wall": "стена с кладовой", "from": "угол у наружной стены (ось 1)", "off": 400},
        {"room": "D1", "type": "eta", "pos": [2500, 8520, Z_GRILLE2], "n": [0, 1], "part": W,
         "wall": "стена с кладовой", "from": "угол у наружной стены (ось 1)", "off": 2300},
        {"room": "D2", "type": "sup", "pos": [11400, 11650, Z_GRILLE2], "n": [1, 0], "part": C,
         "wall": "стена с общим санузлом", "from": "угол у окна (ось Г)", "off": 350},
        {"room": "D2", "type": "eta", "pos": [11400, 9700, Z_GRILLE2], "n": [1, 0], "part": C,
         "wall": "стена с общим санузлом", "from": "угол у окна (ось Г)", "off": 2300},
        {"room": "K1", "type": "sup", "pos": [10900, 11650, Z_CEIL1], "n": [1, 0], "part": C, "reserve": True,
         "wall": "стена с санузлом 1-го эт.", "from": "угол у окна (ось Г)", "off": 350},
        {"room": "K1", "type": "eta", "pos": [10900, 9700, Z_CEIL1], "n": [1, 0], "part": C, "reserve": True,
         "wall": "стена с санузлом 1-го эт.", "from": "угол у окна (ось Г)", "off": 2300},
    ]
    # ---- электрика для вентиляции (на одну половину) ----
    # точки: где оставить кабель / коробку / розетку. pos = [x, y, z], z от пола 1-го этажа
    zl = Z_CEIL2 - 80        # кабели в подшивном потолке (чуть ниже труб)
    zr = ROOF + 100          # кабели на кровле (в защитной гофре/металлорукаве на опорах)
    elec = [
        {"n": 1, "kind": "riser", "pos": [260, 7170, 300], "part": W,
         "name": "Кабельный стояк от щита",
         "where": "1-й эт.: штроба в углу наружной стены (ось 1) под кладовой; 2-й эт.: в шахте А; выход на кровлю",
         "h": "от пола 1-го эт. до кровли", "cable": "гофра ПНД Ø32 (силовые) + Ø25 (слаботочные), раздельно",
         "route": "щит → по 1-му эт. к оси 1 → вверх → шахта А → кровля"},
        {"n": 2, "kind": "isolator", "pos": [4850, 9450, ROOF + 650], "part": W,
         "name": "Питание рекуператора + ремонтный выключатель",
         "where": "на раме рекуператора, с западной стороны", "h": "0,65 м над кровлей",
         "cable": "ВВГнг(А)-LS 5×4 мм² (линия 1)", "route": "щит → стояк (1) → по кровле вдоль труб → выключатель IP65 → агрегат"},
        {"n": 3, "kind": "socket", "pos": [4850, 8850, ROOF + 650], "part": W,
         "name": "Розетка IP65 для обслуживания",
         "where": "на раме рекуператора, рядом с выключателем", "h": "0,65 м над кровлей",
         "cable": "ВВГнг(А)-LS 3×2,5 мм² (линия 2, через УЗО 30 мА)", "route": "щит → стояк (1) → по кровле → розетка"},
        {"n": 4, "kind": "heat", "pos": [5600, 8250, ROOF + 60], "part": W,
         "name": "Обогрев дренажа конденсата",
         "where": "коробка IP65 у розетки (3) → греющий кабель внутри дренажной трубки до водостока",
         "h": "по кровле", "cable": "от линии 2 через коробку; саморегулирующийся кабель 10–20 Вт/м",
         "route": "коробка у агрегата → вдоль дренажа"},
        {"n": 5, "kind": "pult", "pos": [3000, 7120, FL2 + 1500], "part": W, "nrm": [1, 0],
         "name": "Пульт управления (подрозетник)",
         "where": "коридор 2-го эт., на стене кладовой рядом с её дверью", "h": "1,5 м от пола",
         "cable": "витая пара FTP 5e (или 4×0,75 экр., по паспорту)",
         "route": "подрозетник → вверх в стене → потолок кладовой → шахта А → кровля → агрегат"},
        {"n": 6, "kind": "sensor", "room": "R", "pos": [1550, 4855, FL2 + 1500], "part": W, "nrm": [0, -1],
         "name": "Датчик CO₂ (подрозетник), комната родителей",
         "where": "стена с санузлом, под решёткой вытяжки", "h": "1,5 м от пола",
         "cable": "витая пара FTP 5e", "route": "подрозетник → вверх → потолок с/у → шахта А → кровля → агрегат"},
        {"n": 7, "kind": "sensor", "room": "D1", "pos": [2500, 8520, FL2 + 1500], "part": W, "nrm": [0, 1],
         "name": "Датчик CO₂ (подрозетник), детская в крыле",
         "where": "стена с кладовой, под решёткой вытяжки", "h": "1,5 м от пола",
         "cable": "витая пара FTP 5e", "route": "подрозетник → вверх → потолок кладовой → шахта А → кровля → агрегат"},
        {"n": 8, "kind": "sensor", "room": "D2", "pos": [11400, 9700, FL2 + 1500], "part": C, "nrm": [1, 0],
         "name": "Датчик CO₂ (подрозетник), детская в центре",
         "where": "стена с общим санузлом, под решёткой вытяжки", "h": "1,5 м от пола",
         "cable": "витая пара FTP 5e", "route": "подрозетник → вверх → потолок с/у → шахта Б → кровля → агрегат"},
        {"n": 9, "kind": "sensor", "room": "K1", "pos": [10900, 9700, 1500], "part": C, "nrm": [1, 0], "reserve": True,
         "name": "Датчик CO₂ (резерв), комната 1-го эт.",
         "where": "стена с санузлом 1-го эт., под решёткой вытяжки", "h": "1,5 м от пола",
         "cable": "витая пара FTP 5e", "route": "подрозетник → потолок с/у 1-го эт. → шахта Б → кровля → агрегат"},
    ]
    w, c = W, C
    wires = [
        # силовые: стояк и кровля
        {"kind": "power", "pts": [[260, 7170, 300, w], [260, 7170, zr, w], [260, 7450, zr, w], [4400, 7450, zr, w],
                                   [4400, 9450, zr, w], [4850, 9450, zr, w], [4850, 9450, ROOF + 650, w]]},
        {"kind": "power", "pts": [[4400, 8850, zr, w], [4850, 8850, zr, w], [4850, 8850, ROOF + 650, w]]},
        {"kind": "heat", "pts": [[4850, 8850, ROOF + 500, w], [5600, 8850, ROOF + 300, w], [5600, 8250, ROOF + 60, w]]},
        # слаботочка: шахта А -> агрегат, шахта Б -> агрегат
        {"kind": "lv", "pts": [[600, 7180, zl, w], [600, 7180, zr, w], [600, 7600, zr, w], [4250, 7600, zr, w],
                                [4250, 9600, zr, w], [4900, 9600, zr, w], [4900, 9600, ROOF + 400, w]]},
        {"kind": "lv", "pts": [[10600, 10700, zl, c], [10600, 10700, zr, c], [10750, 10700, zr, c], [10750, 9650, zr, c],
                                [6300, 9650, zr, w], [6300, 9650, ROOF + 400, w]]},
        # слаботочка внутри 2-го этажа (в стенах и подшивных потолках)
        {"kind": "lv", "pts": [[3000, 7120, FL2 + 1500, w], [3000, 7120, zl, w], [600, 7120, zl, w]]},
        {"kind": "lv", "pts": [[1550, 4855, FL2 + 1500, w], [1550, 4855, zl, w], [1550, 5050, zl, w], [750, 5050, zl, w],
                                [750, 7100, zl, w], [600, 7100, zl, w]]},
        {"kind": "lv", "pts": [[2500, 8520, FL2 + 1500, w], [2500, 8520, zl, w], [2500, 8250, zl, w], [750, 8250, zl, w],
                                [750, 7250, zl, w], [600, 7250, zl, w]]},
        {"kind": "lv", "pts": [[11400, 9700, FL2 + 1500, c], [11400, 9700, zl, c], [10900, 9700, zl, c],
                                [10900, 10700, zl, c], [10600, 10700, zl, c]]},
        {"kind": "lv", "reserve": True, "pts": [[10900, 9700, 1500, c], [10900, 9700, Z_CEIL1, c], [10750, 9700, Z_CEIL1, c],
                                                 [10750, 10700, Z_CEIL1, c], [10600, 10700, Z_CEIL1, c], [10600, 10700, zl, c]]},
    ]
    return rooms, unit, shafts, ducts, grilles, elec, wires


def side(sign):
    rooms, unit, shafts, ducts, grilles, elec, wires = left_side()
    tag = "Л" if sign == "L" else "П"
    if sign == "R":
        ax = lambda part: WING_AXIS if part == "wing" else CENTER_AXIS
        unit = dict(unit, rect=mirror_rect(unit["rect"], WING_AXIS))
        shafts = [dict(s, rect=mirror_rect(s["rect"], ax(s["part"]))) for s in shafts]
        # трасса кровли до шахты Б: первая точка (у агрегата) — по оси крыла, остальные — по оси центра
        def mirror_duct(d):
            axes = [ax(d["part"])] * len(d["pts"])
            if d["zone"] == "roof" and d.get("to") == "Б":
                axes[0] = WING_AXIS
            return dict(d, pts=[mirror_x(p, a) for p, a in zip(d["pts"], axes)])
        ducts = [mirror_duct(d) for d in ducts]
        grilles = [dict(g, pos=mirror_x(g["pos"], ax(g["part"])), n=[-g["n"][0], g["n"][1]]) for g in grilles]
        elec = [dict(e, pos=mirror_x(e["pos"], ax(e["part"])),
                     nrm=[-e["nrm"][0], e["nrm"][1]] if "nrm" in e else None) for e in elec]
        wires = [dict(wi, pts=[mirror_x(p, ax(p[3])) for p in wi["pts"]]) for wi in wires]
    for s in shafts:
        s["name"] = f"Шахта {s['id']}-{tag}"
    unit["name"] = f"Рекуператор {tag}"
    total = sum(r["flow"] for r in rooms.values() if not r["reserve"])
    reserve = sum(r["flow"] for r in rooms.values() if r["reserve"])
    for d in ducts:
        q = flow_of_duct(d, rooms)
        d["flow"] = q
        d["v"] = round(q / 3600 / (math.pi * (d["d"] / 2000) ** 2), 1) if q else None
    for g in grilles:
        g["flow"] = rooms[g["room"]]["flow"]
    return {"side": sign, "tag": tag, "rooms": list(rooms.values()), "unit": unit, "shafts": shafts,
            "ducts": ducts, "grilles": grilles, "elec": elec,
            "wires": [dict(wi, pts=[p[:3] for p in wi["pts"]]) for wi in wires],
            "total": total, "totalWithReserve": total + reserve}


def flow_of_duct(d, rooms):
    if "room" in d:
        return rooms[d["room"]]["flow"]
    if d["type"] in ("oda", "eha"):
        return sum(r["flow"] for r in rooms.values() if not r["reserve"])
    if d.get("to") == "А":
        return rooms["R"]["flow"] + rooms["D1"]["flow"]
    if d.get("to") == "Б":
        return rooms["D2"]["flow"]
    return 0


def data():
    return {
        "unitCapacity": 1000,
        "levels": {"fl2": FL2, "ceiling2": C2, "roof": ROOF, "duct2": Z_CEIL2, "duct1": Z_CEIL1},
        "sides": [side("L"), side("R")],
    }


if __name__ == "__main__":
    import json
    d = data()
    for s in d["sides"]:
        print(s["unit"]["name"], "расход", s["total"], "м³/ч (с резервом", s["totalWithReserve"], ")")
        for r in s["rooms"]:
            print("  ", r["name"], r["flow"])
        for du in s["ducts"]:
            print("   duct", du["type"], du["d"], du.get("room") or du.get("to"), du["flow"], "м³/ч", du["v"], "м/с",
                  du["pts"][0][:2], "->", du["pts"][-1][:2])
    json.dumps(d)

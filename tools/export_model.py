"""Выгрузка модели дома в JSON для 3D-приложения (app/).

Берёт ту же модель, что и make_plan.py (стены, окна, проёмы, помещения,
лестницы и сантехника из PDF), и пишет app/house.json.
Дополнительно режет исходные чертежи в подложки app/underlay-1.jpg / -2.jpg,
выровненные по осям (границы в мм записаны в JSON).

Запуск: python3 tools/export_model.py
"""
import io
import json
import os

import pypdfium2 as pdfium
from PIL import Image

import make_plan as mp

APP = os.path.join(mp.ROOT, "app")

# помещения, у которых нет пола (открытые зоны / проём лестницы на 2-м этаже)
ROOM_KIND = [
    ("С/у", "wet"), ("Лестница", "stair"), ("Холл", "hall"), ("Тамбур", "hall"),
    ("Кладовая", "store"), ("Крыло", "living"), ("Комната", "living"), ("Детская", "living"),
]

# границы подложки в мм (x0, x1, y0, y1)
UNDERLAY_BOX = (-1500, 31200, -1500, 15200)


def kind_of(name):
    for key, k in ROOM_KIND:
        if name.startswith(key):
            return k
    return "outdoor"


def simplify(pts):
    out = []
    for x, y in pts:
        p = [round(x / 5) * 5, round(y / 5) * 5]
        if not out or out[-1] != p:
            out.append(p)
    return out if len(out) > 1 else None


def floor_data(floor):
    for lst in (mp.EXT, mp.PART, mp.COL, mp.WIN, mp.OPEN, mp.ROOMS, mp.EXTRA, mp.GAPS):
        lst.clear()
    (mp.floor1 if floor == 1 else mp.floor2)()
    gaps = list(mp.GAPS)
    if floor == 1:   # широкие проёмы холл -> тамбур (стены заданы двумя кусками)
        gaps += [(4850, 6345, 6600, 7000), (23355, 24850, 6600, 7000)]

    stairs = [(4600, 8495, 8150, 12000), (21195, 25100, 8150, 12000)]
    if floor == 1:
        fixtures = [(8750, 10645, 9050, 12000), (18550, 20950, 9050, 12000)]
    else:
        fixtures = [(8750, 11150, 9300, 12000), (18050, 20950, 9300, 12000),
                    (200, 2880, 4975, 6880), (26820, 29500, 4975, 6880)]
    lines = {"stair": [], "fix": []}
    for kind, pts in mp.pdf_symbols(floor, stairs, fixtures):
        s = simplify(pts)
        if s:
            lines[kind].append(s)

    rooms = []
    for name, rects, dim, (lx, ly) in mp.ROOMS:
        name, _, note = name.partition("|")
        rooms.append({
            "name": name, "note": note, "kind": kind_of(name),
            "rects": [list(r) for r in rects],
            "dim": list(dim) if dim else None,
            "label": [lx, ly],
            "area": round(mp.area(rects), 1) if rects else None,
        })
    return {
        "level": floor,
        "name": "1-й этаж" if floor == 1 else "2-й этаж",
        "elevation": 0 if floor == 1 else 3300,
        "walls": [list(r) for r in mp.EXT],
        "partitions": [list(r) for r in mp.PART],
        "columns": [list(r) for r in mp.COL],
        "windows": [list(r) for r in mp.WIN],
        "gaps": [list(r) for r in gaps],
        "rooms": rooms,
        "roofs": [list(r) for _, r in mp.EXTRA],
        "lines": lines,
        "underlay": {"box": list(UNDERLAY_BOX), "src": f"underlay-{floor}.jpg"},
    }


def underlay(floor, path, px_per_m=60):
    """Вырезает область плана из PDF, выровненную по осям, в JPEG."""
    pdf = pdfium.PdfDocument(mp.SRC[floor])
    page = pdf[0]
    x0, x1, y0, y1 = UNDERLAY_BOX
    # мм -> pt
    pt_x0, pt_x1 = mp.AX1 + x0 / mp.K, mp.AX1 + x1 / mp.K
    pt_top, pt_bot = mp.AXA - y1 / mp.K, mp.AXA - y0 / mp.K
    scale = px_per_m * (x1 - x0) / 1000 / (pt_x1 - pt_x0)   # пикселей на pt
    img = page.render(scale=scale).to_pil()
    # pypdfium рендерит с учётом /Rotate — координаты как у pdfplumber
    box = tuple(int(round(v * scale)) for v in (pt_x0, pt_top, pt_x1, pt_bot))
    img = img.crop(box).convert("RGB")
    img.save(path, "JPEG", quality=72, optimize=True)
    return img.size


if __name__ == "__main__":
    os.makedirs(APP, exist_ok=True)
    house = {
        "name": "Частный дом, г. Ташкент",
        "source": "КЖ 2022, листы 9.1 (отм. 0,000) и 9.2 (отм. +3,300)",
        "units": "mm",
        "floorHeight": 3300,
        "slab": 250,
        "floors": [floor_data(1), floor_data(2)],
        "site": {"yard": [4600, 25100, 200, 6600], "innerYard": [4600, 25100, 12400, 13900],
                 "fence": [[-205, 14400], [29905, 14175]]},
    }
    with open(os.path.join(APP, "house.json"), "w", encoding="utf-8") as fh:
        json.dump(house, fh, ensure_ascii=False, separators=(",", ":"))
    for f in (1, 2):
        print("underlay", f, underlay(f, os.path.join(APP, f"underlay-{f}.jpg")))
    print("ok", os.path.getsize(os.path.join(APP, "house.json")))

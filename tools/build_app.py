"""Собирает app/index.html: подставляет app/house.json и подложки-чертежи (data URI).

Запуск: python3 tools/export_model.py && python3 tools/build_app.py
"""
import base64
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP = os.path.join(ROOT, "app")

src = open(os.path.join(APP, "index.src.html"), encoding="utf-8").read()
house = open(os.path.join(APP, "house.json"), encoding="utf-8").read()
out = src.replace("__HOUSE_JSON__", house)
for f in (1, 2):
    with open(os.path.join(APP, f"underlay-{f}.jpg"), "rb") as fh:
        out = out.replace(f"__UNDERLAY_{f}__", "data:image/jpeg;base64," + base64.b64encode(fh.read()).decode())
with open(os.path.join(APP, "index.html"), "w", encoding="utf-8") as fh:
    fh.write(out)
print("app/index.html", len(out) // 1024, "KB")

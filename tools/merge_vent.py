"""Склеивает листы вентиляции в plan/ventilyaciya.pdf (после render_vent.js)."""
import os
from pypdf import PdfReader, PdfWriter

d = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "plan")
plans = PdfReader(os.path.join(d, "_vent-plans.pdf"))
w = PdfWriter()
w.add_page(plans.pages[0])          # 2-й этаж
w.add_page(plans.pages[1])          # двор
w.append(os.path.join(d, "_vent-fasad.pdf"))   # фасад и разрез
w.add_page(plans.pages[2])          # электрика
w.add_page(plans.pages[3])          # 1-й этаж, резерв
w.append(os.path.join(d, "_vent-spec.pdf"))    # спецификация
w.write(os.path.join(d, "ventilyaciya.pdf"))
for f in ("_vent-plans.pdf", "_vent-fasad.pdf", "_vent-spec.pdf"):
    os.remove(os.path.join(d, f))
print("pages:", len(w.pages))

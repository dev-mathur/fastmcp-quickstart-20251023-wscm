#!/usr/bin/env python3
"""Tiny helper for drawing the article diagrams as theme-aware SVG (light and dark).

    from svgfig import Fig
    f = Fig(720, 360)
    f.box(20, 20, 200, 60, "Label", cls="accent")
    f.text(360, 200, "Caption", anchor="middle")
    f.arrow(220, 50, 300, 50)
    f.save("public/figures/<slug>/<name>.svg")
"""
from __future__ import annotations
from xml.sax.saxutils import escape

STYLE = """
:root{--paper:#ffffff;--wash:#f6f6f3;--ink:#18181b;--ink2:#52525b;--line:#c9c9c2;--accent:#2b50d8;--accentwash:#eef1fd;--warn:#b4531a;--warnwash:#fbeee3}
@media (prefers-color-scheme:dark){:root{--paper:#1a1a1d;--wash:#222226;--ink:#ececee;--ink2:#a8a8b0;--line:#3a3a40;--accent:#8aa3ff;--accentwash:#1b2140;--warn:#f0a070;--warnwash:#3a2a1f}}
text{font-family:Inter,system-ui,-apple-system,'Segoe UI',Roboto,sans-serif;fill:var(--ink);font-size:15px}
.t2{fill:var(--ink2);font-size:13px}.tb{font-weight:600}.ta{fill:var(--accent);font-weight:600}
.box{fill:var(--paper);stroke:var(--line);stroke-width:1.5}
.accent{fill:var(--accentwash);stroke:var(--accent);stroke-width:1.5}
.warn{fill:var(--warnwash);stroke:var(--warn);stroke-width:1.5}
.wash{fill:var(--wash);stroke:var(--line);stroke-width:1.5}
.ln{stroke:var(--ink2);stroke-width:1.6;fill:none}.lna{stroke:var(--accent);stroke-width:2;fill:none}
.head{fill:var(--ink2)}.headaccent{fill:var(--accent)}
"""

class Fig:
    def __init__(self, w, h, title="", desc=""):
        self.w, self.h = w, h
        self.title, self.desc = title, desc
        self.parts = []

    def _lines(self, s, size_cls):
        return s.split("\n")

    def text(self, x, y, s, anchor="start", cls="", lh=19):
        lines = s.split("\n")
        out = []
        for i, line in enumerate(lines):
            out.append(f'<tspan x="{x}" dy="{0 if i == 0 else lh}">{escape(line)}</tspan>')
        self.parts.append(f'<text x="{x}" y="{y}" text-anchor="{anchor}" class="{cls}">{"".join(out)}</text>')

    def box(self, x, y, w, h, label="", cls="box", textcls="", sub="", rx=8):
        self.parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" class="{cls}"/>')
        if label:
            lines = label.count("\n") + 1
            ty = y + h / 2 + 5 - (lines - 1) * 9.5 - (8 if sub else 0)
            self.text(x + w / 2, ty, label, "middle", textcls)
        if sub:
            self.text(x + w / 2, y + h / 2 + 5 + (label.count("\n")) * 9.5 + 12, sub, "middle", "t2")

    def line(self, x1, y1, x2, y2, cls="ln"):
        self.parts.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" class="{cls}"/>')

    def arrow(self, x1, y1, x2, y2, cls="ln"):
        self.parts.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" class="{cls}" marker-end="url(#ah)"/>')

    def poly(self, pts, cls="box"):
        p = " ".join(f"{x},{y}" for x, y in pts)
        self.parts.append(f'<polygon points="{p}" class="{cls}"/>')

    def circle(self, cx, cy, r, cls="box"):
        self.parts.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" class="{cls}"/>')

    def raw(self, s):
        self.parts.append(s)

    def svg(self):
        head = (
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.w} {self.h}" role="img" '
            f'aria-label="{escape(self.title)}">'
            f'<title>{escape(self.title)}</title><desc>{escape(self.desc)}</desc>'
            f'<style>{STYLE}</style>'
            '<defs><marker id="ah" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
            '<path d="M0,0 L10,5 L0,10 z" style="fill:var(--ink2)"/></marker></defs>'
        )
        return head + "".join(self.parts) + "</svg>\n"

    def save(self, path):
        import os
        os.makedirs(os.path.dirname(path), exist_ok=True)
        open(path, "w").write(self.svg())

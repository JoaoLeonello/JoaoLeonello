"""Render a donut chart of the owner's languages (public, non-fork repos) in bitwise-ops colors.

Usage: GITHUB_TOKEN=... python3 scripts/langs.py <user> <out.svg>
"""

import json
import math
import os
import sys
import urllib.request
from collections import Counter

# build/markup files say little about what I write
IGNORED = {"Dockerfile", "Makefile", "HTML", "CSS", "SCSS", "Procfile", "Batchfile"}
TOP = 5
# site palette: green accents, zinc neutrals
SLICES = ["#4ade80", "#22c55e", "#86efac", "#16a34a", "#bbf7d0"]
OTHER = "#52525b"
BG, BORDER, TEXT, MUTED = "#000000", "#27272a", "#d4d4d8", "#71717a"


def api(path):
    req = urllib.request.Request(f"https://api.github.com{path}")
    if token := os.environ.get("GITHUB_TOKEN"):
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req) as r:
        return json.load(r)


def languages(user):
    totals = Counter()
    page = 1
    while repos := api(f"/users/{user}/repos?per_page=100&type=owner&page={page}"):
        for repo in repos:
            if not repo["fork"]:
                totals.update(api(f"/repos/{user}/{repo['name']}/languages"))
        page += 1
    return totals


def shares(totals):
    totals = {k: v for k, v in totals.items() if k not in IGNORED}
    total = sum(totals.values())
    ranked = sorted(totals.items(), key=lambda kv: -kv[1])
    out = [(name, n / total) for name, n in ranked[:TOP]]
    rest = sum(n for _, n in ranked[TOP:])
    if rest:
        out.append(("Other", rest / total))
    return out


def arc(cx, cy, r, start, end):
    # angles in turns, 0 = 12 o'clock, clockwise
    def point(t):
        a = 2 * math.pi * t - math.pi / 2
        return cx + r * math.cos(a), cy + r * math.sin(a)

    (x0, y0), (x1, y1) = point(start), point(end)
    large = 1 if end - start > 0.5 else 0
    return f"M{x0:.2f},{y0:.2f} A{r},{r} 0 {large} 1 {x1:.2f},{y1:.2f}"


def render(data):
    # same 500x320 box as the LeetCode card so they sit side by side
    w, h, cx, cy, r = 500, 320, 115, 180, 72
    parts, legend, t = [], [], 0.0
    for i, (name, share) in enumerate(data):
        color = OTHER if name == "Other" else SLICES[i % len(SLICES)]
        if share >= 0.999:  # a single 360° arc would collapse to a point
            parts.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{color}" stroke-width="30"/>')
        else:
            parts.append(f'<path d="{arc(cx, cy, r, t, t + share)}" fill="none" stroke="{color}" stroke-width="30"/>')
        t += share
        y = 104 + i * 32
        bar = round(share * 120)
        legend.append(
            f'<rect x="230" y="{y - 10}" width="10" height="10" fill="{color}"/>'
            f'<text x="248" y="{y}" class="n">{name}</text>'
            f'<rect x="345" y="{y - 8}" width="120" height="6" fill="{BORDER}"/>'
            f'<rect x="345" y="{y - 8}" width="{bar}" height="6" fill="{color}"/>'
            f'<text x="345" y="{y + 14}" class="p">{share * 100:.1f}%</text>'
        )
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="Most used languages">
  <style>
    text {{ font-family: "JetBrains Mono", "Fira Code", "Courier New", monospace; font-size: 13px; }}
    .n {{ fill: {TEXT}; }}
    .p {{ fill: {MUTED}; font-size: 11px; }}
    .h {{ fill: #4ade80; font-size: 20px; font-weight: 700; }}
  </style>
  <rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="10" fill="{BG}" stroke="{BORDER}"/>
  <text x="24" y="44" class="h">$ ls ./langs --top {TOP}</text>
  <line x1="24" y1="58" x2="{w - 24}" y2="58" stroke="{BORDER}"/>
  <circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{BORDER}" stroke-width="30"/>
  {"".join(parts)}
  {"".join(legend)}
</svg>
"""


if __name__ == "__main__":
    user, out = sys.argv[1], sys.argv[2]
    data = shares(languages(user))
    assert abs(sum(s for _, s in data) - 1) < 1e-9, data
    with open(out, "w") as f:
        f.write(render(data))

"""Render a bar list of the owner's languages (public, non-fork repos) in bitwise-ops colors.

Usage: GITHUB_TOKEN=... python3 scripts/langs.py <user> <out.svg>
"""

import json
import os
import sys
import urllib.request
from collections import Counter

# build/markup files say little about what I write
IGNORED = {"Dockerfile", "Makefile", "HTML", "CSS", "SCSS", "Procfile", "Batchfile"}
TOP = 5
# site palette: green accents, zinc neutrals
GREEN, OTHER = "#4ade80", "#52525b"
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


def render(data):
    # same 500x320 box as the LeetCode card so they sit side by side
    w, h = 500, 320
    rows = []
    for i, (name, share) in enumerate(data):
        color = OTHER if name == "Other" else GREEN
        y = 104 + i * 38
        rows.append(
            f'<text x="24" y="{y}" class="n">{name}</text>'
            f'<rect x="150" y="{y - 9}" width="260" height="8" rx="2" fill="{BORDER}"/>'
            f'<rect x="150" y="{y - 9}" width="{round(share * 260)}" height="8" rx="2" fill="{color}"/>'
            f'<text x="{w - 24}" y="{y}" class="p" text-anchor="end">{share * 100:.1f}%</text>'
        )
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="Most used languages">
  <style>
    text {{ font-family: "JetBrains Mono", "Fira Code", "Courier New", monospace; font-size: 14px; }}
    .n {{ fill: {TEXT}; }}
    .p {{ fill: {MUTED}; }}
    .h {{ fill: {GREEN}; font-size: 20px; font-weight: 700; }}
  </style>
  <rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="10" fill="{BG}" stroke="{BORDER}"/>
  <text x="24" y="44" class="h">$ ls ./langs --top {TOP}</text>
  <line x1="24" y1="58" x2="{w - 24}" y2="58" stroke="{BORDER}"/>
  {"".join(rows)}
</svg>
"""


if __name__ == "__main__":
    user, out = sys.argv[1], sys.argv[2]
    data = shares(languages(user))
    assert abs(sum(s for _, s in data) - 1) < 1e-9, data
    with open(out, "w") as f:
        f.write(render(data))

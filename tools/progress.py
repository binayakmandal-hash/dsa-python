"""Draws the progress card shown at the top of the README.

    python tools/progress.py dist

Reads the header of every file in solutions/ and writes progress-light.svg and progress-dark.svg:
total solved, a tally for each difficulty, the current daily streak, and how far each topic has got.
GitHub Actions runs this on every push and publishes the cards to the `output` branch.
"""
import datetime
import math
import pathlib
import random
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
HERE = pathlib.Path(__file__).parent

THEMES = {
    "light": dict(bg="#E9EDF1", panel="#F5F7F9", ink="#22303F", soft="#5B6878", faint="#C9D2DB",
                  teal="#2F6F73", tealsoft="#8DB8B6", amber="#C98A12", easy="#2F6F73", medium="#C98A12", hard="#B5523B"),
    "dark": dict(bg="#182029", panel="#1E2833", ink="#E3E9EF", soft="#93A1B0", faint="#33414F",
                 teal="#6FB3B1", tealsoft="#3E6E6D", amber="#E8B14A", easy="#6FB3B1", medium="#E8B14A", hard="#E08A6F"),
}


def read_header(path):
    """Returns the 'Key: value' lines from the docstring at the top of a solution file."""
    text = path.read_text(encoding="utf-8")
    m = re.match(r'\s*"""(.*?)"""', text, re.S)
    info = {}
    if m:
        for line in m.group(1).splitlines():
            for part in re.split(r"\s{3,}", line.strip()):  # "Time: O(n)    Space: O(1)" on one line
                k, sep, v = part.partition(":")
                if sep and k.strip() in {"Problem", "Link", "Difficulty", "Topic", "Solved", "Time", "Space"}:
                    info[k.strip()] = v.strip()
    return info


def collect():
    topics = sorted(p.name for p in (ROOT / "solutions").iterdir() if p.is_dir())
    rows = []
    for f in (ROOT / "solutions").rglob("*.py"):
        info = read_header(f)
        try:
            day = datetime.date.fromisoformat(info.get("Solved", ""))
        except ValueError:
            continue
        rows.append(dict(topic=f.parent.name, difficulty=info.get("Difficulty", "").lower(), day=day))
    by_diff = {d: sum(r["difficulty"] == d for r in rows) for d in ("easy", "medium", "hard")}
    by_topic = {t: sum(r["topic"] == t for r in rows) for t in topics}
    days = {r["day"] for r in rows}
    today = datetime.date.today()
    streak, d = 0, today if today in days else today - datetime.timedelta(days=1)
    while d in days:
        streak += 1
        d -= datetime.timedelta(days=1)
    return dict(total=len(rows), diff=by_diff, topics=by_topic, streak=streak, active_days=len(days))


def wobble(points, seed, amt=0.6):
    rnd = random.Random(seed)
    pts = [(x + rnd.uniform(-amt, amt), y + rnd.uniform(-amt, amt)) for x, y in points]
    d = f"M{pts[0][0]:.1f},{pts[0][1]:.1f}"
    for k in range(1, len(pts) - 1, 2):
        (cx, cy), (x, y) = pts[k], pts[min(k + 1, len(pts) - 1)]
        d += f" Q{cx:.1f},{cy:.1f} {x:.1f},{y:.1f}"
    return d


def circle(cx, cy, rx, ry, seed):
    rnd = random.Random(seed)
    pts = []
    for k in range(33):
        th = -0.6 + k / 32 * 2.15 * math.pi
        f = 1 + rnd.uniform(-.04, .04) + .05 * k / 32
        pts.append((cx + rx * f * math.cos(th), cy + ry * f * math.sin(th)))
    return wobble(pts, seed, .5)


def tally(x, y, n, color, seed, limit=30):
    """Hand-drawn tally marks in groups of five, like counting on paper."""
    rnd = random.Random(seed)
    out, shown = [], min(n, limit)
    for g in range(math.ceil(shown / 5)):
        in_group = min(5, shown - g * 5)
        gx = x + g * 44
        for k in range(min(in_group, 4)):
            lx = gx + k * 8 + rnd.uniform(-1, 1)
            out.append(f'<path d="M{lx:.1f},{y + rnd.uniform(-1, 1):.1f} L{lx + rnd.uniform(-1.5, 1.5):.1f},{y + 26:.1f}" '
                       f'stroke="{color}" stroke-width="2.4" stroke-linecap="round"/>')
        if in_group == 5:
            out.append(f'<path d="M{gx - 4:.1f},{y + 20:.1f} L{gx + 30:.1f},{y + 5:.1f}" stroke="{color}" stroke-width="2.4" stroke-linecap="round"/>')
    return "".join(out), (x + math.ceil(shown / 5) * 44 if shown else x)


def render(s, c, fonts):
    W, H = 1000, 340
    css = fonts + f"""
.n{{font-family:Hand;font-weight:600;font-size:64px;fill:{c['amber']}}}
.m{{font-family:Hand;font-weight:600;font-size:26px;fill:{c['ink']}}}
.l{{font-family:Bric;font-weight:500;font-size:16px;fill:{c['ink']}}}
.s{{font-family:Bric;font-weight:500;font-size:13.5px;fill:{c['soft']}}}
.h{{font-family:Hand;font-weight:600;font-size:23px;fill:{c['soft']}}}
"""
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" '
           f'aria-label="{s["total"]} problems solved: {s["diff"]["easy"]} easy, {s["diff"]["medium"]} medium, '
           f'{s["diff"]["hard"]} hard. Current streak {s["streak"]} days.">'
           f'<title>Progress</title><style>{css}</style>',
           f'<rect width="{W}" height="{H}" rx="16" fill="{c["bg"]}"/>']
    # total, circled
    t = str(s["total"])
    out.append(f'<text class="n" x="52" y="104">{t}</text>')
    w = 28 * len(t) + 6
    out.append(f'<path d="{circle(52 + w / 2, 83, w / 2 + 18, 36, 2)}" fill="none" stroke="{c["amber"]}" stroke-width="2" stroke-linecap="round"/>')
    out.append(f'<text class="l" x="52" y="150">problems solved</text>')
    days_line = f'on {s["active_days"]} different days' if s["total"] else "the first one starts the streak"
    out.append(f'<text class="s" x="52" y="172">{days_line}</text>')
    out.append(f'<text class="m" x="52" y="232">{s["streak"]} day streak</text>')
    out.append(f'<path d="{wobble([(52, 242), (120, 244), (190, 241)], 3, .6)}" fill="none" stroke="{c["amber"]}" stroke-width="2.5" stroke-linecap="round"/>')
    # tallies per difficulty
    for k, d in enumerate(("easy", "medium", "hard")):
        y = 36 + k * 50
        out.append(f'<text class="l" x="250" y="{y + 19}">{d.capitalize()}</text>')
        marks, end = tally(330, y, s["diff"][d], c[d], 10 + k)
        out.append(marks)
        extra = s["diff"][d] - 30
        label = f'{s["diff"][d]}' + (f' (+{extra} not drawn)' if extra > 0 else "")
        out.append(f'<text class="s" x="{end + 6 if s["diff"][d] else 330}" y="{y + 19}">{label if s["diff"][d] else "none yet"}</text>')
    # topics: one small box each, filled as it gets practice
    tx, ty, cw, ch = 250, 228, 56, 50
    out.append(f'<text class="s" x="{tx}" y="{ty - 12}">by topic (box fills at 10 problems)</text>')
    for k, (name, n) in enumerate(s["topics"].items()):
        x = tx + k * cw
        fill = min(n / 10, 1)
        out.append(f'<rect x="{x}" y="{ty}" width="{cw - 8}" height="{ch - 18}" rx="5" fill="{c["panel"]}" stroke="{c["faint"]}"/>')
        if fill:
            fh = (ch - 18) * fill
            out.append(f'<rect x="{x}" y="{ty + ch - 18 - fh:.1f}" width="{cw - 8}" height="{fh:.1f}" rx="5" fill="{c["tealsoft"]}"/>')
        out.append(f'<text class="s" x="{x + (cw - 8) / 2}" y="{ty + 21}" text-anchor="middle" fill="{c["ink"]}">{n}</text>')
        short = {"arrays-hashing": "arrays", "two-pointers": "2 ptrs", "sliding-window": "window", "binary-search": "bsearch",
                 "linked-list": "linked", "dynamic-programming": "dp", "backtracking": "backtrk", "math-bits": "math"}.get(name, name)
        out.append(f'<text class="s" x="{x + (cw - 8) / 2}" y="{ty + ch + 2}" text-anchor="middle" font-size="11">{short}</text>')
    if s["total"] == 0:
        out.append(f'<text class="h" x="{W - 30}" y="{H - 16}" text-anchor="end">empty page. first problem goes here</text>')
    else:
        out.append(f'<text class="h" x="{W - 30}" y="{H - 16}" text-anchor="end">redrawn on every push</text>')
    out.append("</svg>")
    return "\n".join(out)


def main():
    out_dir = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "dist")
    out_dir.mkdir(parents=True, exist_ok=True)
    s = collect()
    fonts = (HERE / "fonts.css").read_text()
    for name, c in THEMES.items():
        (out_dir / f"progress-{name}.svg").write_text(render(s, c, fonts))
    print(f"{s['total']} solved, streak {s['streak']}, by difficulty {s['diff']}")


if __name__ == "__main__":
    main()

"""Start a new problem file from the template.

    python tools/new.py "Two Sum" --topic arrays-hashing --difficulty easy --link https://leetcode.com/problems/two-sum/

Creates solutions/arrays-hashing/two_sum.py with today's date filled in, ready for your solution.
"""
import argparse
import datetime
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
TOPICS = sorted(p.name for p in (ROOT / "solutions").iterdir() if p.is_dir())


def main():
    ap = argparse.ArgumentParser(description="Start a new problem file.")
    ap.add_argument("name", help='problem name, e.g. "Two Sum"')
    ap.add_argument("--topic", required=True, choices=TOPICS)
    ap.add_argument("--difficulty", required=True, choices=["easy", "medium", "hard"])
    ap.add_argument("--link", default="")
    args = ap.parse_args()

    slug = re.sub(r"[^a-z0-9]+", "_", args.name.lower()).strip("_")
    path = ROOT / "solutions" / args.topic / f"{slug}.py"
    if path.exists():
        raise SystemExit(f"{path.relative_to(ROOT)} already exists")

    text = (ROOT / "template.py").read_text()
    text = (text.replace("<name>", args.name)
                .replace("<url>", args.link or "-")
                .replace("<Easy | Medium | Hard>", args.difficulty.capitalize())
                .replace("<folder name, e.g. arrays-hashing>", args.topic)
                .replace("<YYYY-MM-DD>", datetime.date.today().isoformat()))
    path.write_text(text)
    print(f"created {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()

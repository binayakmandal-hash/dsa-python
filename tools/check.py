"""Run every solution's own checks and make sure each file has a filled-in header.

    python tools/check.py

Exits with an error if any solution fails, so GitHub Actions shows a red mark on that commit.
"""
import pathlib
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from progress import read_header  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
REQUIRED = ["Problem", "Difficulty", "Topic", "Solved", "Time"]


def main():
    files = sorted((ROOT / "solutions").rglob("*.py"))
    failed = []
    for f in files:
        rel = f.relative_to(ROOT)
        info = read_header(f)
        missing = [k for k in REQUIRED if not info.get(k) or info[k].startswith("<")]
        if missing:
            failed.append(rel)
            print(f"[header] {rel}: fill in {', '.join(missing)}")
            continue
        r = subprocess.run([sys.executable, str(f)], capture_output=True, text=True, timeout=60)
        if r.returncode != 0:
            failed.append(rel)
            print(f"[fail]   {rel}\n{r.stderr.strip()}")
        else:
            print(f"[ok]     {rel}")
    print(f"\n{len(files) - len(failed)} of {len(files)} solutions passed")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()

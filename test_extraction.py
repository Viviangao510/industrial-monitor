"""Test that Claude reads the reports correctly, without changing any of your data.

    python3 test_extraction.py            (tests Q2 2026, which we already checked by hand)

It downloads the Q2 2026 reports, has Claude read them, and compares every number
with the ones already in data/history.json. Your real data files are not touched.
Cost: about 6 Claude calls, well under $1.
"""
import copy
import json
import shutil
import sys
import tempfile
from pathlib import Path

import config
from scripts import extract, fetch_reports

Q = sys.argv[1] if len(sys.argv) > 1 else "2026Q2"
FIELDS = ["inv", "vac", "rent", "abs_q", "del_ytd", "uc"]


def close(a, b):
    if a is None or b is None:
        return a is None and b is None
    return abs(a - b) <= max(abs(b) * 0.005, 0.051)


def main():
    real = json.loads((config.DATA / "history.json").read_text())
    tmp = Path(tempfile.mkdtemp()) / "history.json"
    shutil.copy(config.DATA / "history.json", tmp)
    extract.HISTORY = tmp  # all writes go to the temporary copy

    print(f"1. Getting the {Q} reports")
    if not fetch_reports.fetch(Q):
        sys.exit("Some reports are missing. Download them by hand as shown above, then run this again.")

    print("\n2. Claude is reading them (about 1–2 minutes)")
    extract.run(Q)
    test = json.loads(tmp.read_text())

    print("\n3. Comparing with the numbers already checked by hand")
    good = bad = 0
    for mid, m in real["metros"].items():
        want, got = m["series"].get(Q, {}), test["metros"].get(mid, {}).get("series", {}).get(Q, {})
        for f in FIELDS:
            if close(got.get(f), want.get(f)):
                good += 1
            else:
                bad += 1
                print(f"  ✗ {m['name_en']} {f}: Claude read {got.get(f)}, expected {want.get(f)}")
        want_s = {s["name"]: s for s in m.get("submarkets", {}).get(Q, [])}
        got_s = {s["name"]: s for s in test["metros"].get(mid, {}).get("submarkets", {}).get(Q, [])}
        for name, w in want_s.items():
            g = got_s.get(name)
            if not g:
                bad += 1
                print(f"  ✗ {m['name_en']} / {name}: submarket not found")
                continue
            for f in ["inv", "vac", "rent"]:
                if w.get(f) is None or close(g.get(f), w.get(f)):
                    good += 1
                else:
                    bad += 1
                    print(f"  ✗ {m['name_en']} / {name} {f}: Claude read {g.get(f)}, expected {w.get(f)}")
    print(f"\nResult: {good} numbers matched, {bad} didn't.")
    print("Your data files were not changed." if bad else "Everything matched. Your data files were not changed.")


if __name__ == "__main__":
    main()

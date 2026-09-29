"""Run the whole quarterly update in one go.

    python run_quarter.py 2026Q3

Steps:
  1. fetch      download the Cushman reports for that quarter
  2. extract    Claude reads the PDFs and the numbers go into data/history.json
  3. check      numbers are checked; problems are listed in data/checks/2026Q3.txt
  4. summarize  Claude writes each city's market update (English + Chinese)
  5. build      site/index.html is rebuilt

Options:
  --build-only   skip steps 1-4 and just rebuild the page from the data you have
  --skip-fetch   use PDFs already saved in data/raw/<quarter>/
  --auto         pick the latest finished quarter; stop quietly if it's already
                 done or Cushman hasn't published it yet (used by the GitHub schedule)
"""
import argparse
import datetime
import json
import sys

import config
from scripts import build_site, check, extract, fetch_reports, summarize


def main():
    ap = argparse.ArgumentParser(description="Quarterly update for the Industrial Market Monitor")
    ap.add_argument("quarter", nargs="?", help="e.g. 2026Q3")
    ap.add_argument("--build-only", action="store_true")
    ap.add_argument("--skip-fetch", action="store_true")
    ap.add_argument("--auto", action="store_true")
    a = ap.parse_args()

    if a.auto:
        today = datetime.date.today()
        a.quarter = config.prev_quarter(config.qkey(today.year, (today.month - 1) // 3 + 1))
        done = json.loads((config.DATA / "history.json").read_text()).get("quarters", [])
        if a.quarter in done:
            print(f"{a.quarter} is already in the data. Nothing to do.")
            return
        y, q = config.parse_quarter(a.quarter)
        folder = config.RAW / a.quarter
        folder.mkdir(parents=True, exist_ok=True)
        if not (folder / "national.pdf").exists() and fetch_reports._download(
                config.NATIONAL_URL.format(y=y, q=q), folder / "national.pdf"):
            print(f"Cushman hasn't published the {a.quarter} national report yet. Will try again next time.")
            return

    if a.build_only:
        build_site.build(a.quarter.upper() if a.quarter else None)
        return
    if not a.quarter:
        sys.exit("Tell me which quarter, e.g.  python run_quarter.py 2026Q3")
    q = config.qkey(*config.parse_quarter(a.quarter))

    if not a.skip_fetch:
        print(f"\n1. Downloading reports for {q}")
        if not fetch_reports.fetch(q):
            sys.exit("\nStopped: some reports are missing (see above).")
    print(f"\n2. Reading the reports with Claude")
    extract.run(q)
    print(f"\n3. Checking the numbers")
    problems = check.run(q)
    print(f"\n4. Writing market updates")
    summarize.run(q)
    print(f"\n5. Building the dashboard")
    out = build_site.build(q)
    print(f"\nDone. Open {out} in your browser.")
    if problems:
        print(f"There are {len(problems)} problem(s) to look at in data/checks/{q}.txt before you share it.")


if __name__ == "__main__":
    main()

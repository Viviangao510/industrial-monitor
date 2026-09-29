"""Step 1: download the Cushman & Wakefield PDF reports for one quarter.

Saves to data/raw/<quarter>/national.pdf and data/raw/<quarter>/<metro>.pdf.
If a download fails (Cushman changes file names, or blocks the request),
it prints the page where you can download the PDF by hand and the exact
file name to save it as. The rest of the pipeline works the same either way.
"""
import sys
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import config  # noqa: E402

HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36"}


def _download(url, dest):
    try:
        r = requests.get(url, headers=HEADERS, timeout=60)
    except requests.RequestException as e:
        return f"network error: {e}"
    if r.status_code != 200 or not r.content.startswith(b"%PDF"):
        return f"HTTP {r.status_code}"
    dest.write_bytes(r.content)
    return None


def fetch(quarter):
    y, q = config.parse_quarter(quarter)
    folder = config.RAW / quarter
    folder.mkdir(parents=True, exist_ok=True)
    missing = []

    targets = [("national", [config.NATIONAL_URL], config.NATIONAL_PAGE)]
    targets += [(mid, m["local_urls"], m["local_page"]) for mid, m in config.METROS.items()]

    for name, patterns, page in targets:
        dest = folder / f"{name}.pdf"
        if dest.exists():
            print(f"  ✓ {name}: already have {dest.name}")
            continue
        err = None
        known = config.KNOWN_URLS.get(quarter, {}).get(name)
        for pat in ([known] if known else []) + patterns:
            err = _download(pat.format(y=y, q=q), dest)
            if err is None:
                print(f"  ✓ {name}: downloaded")
                break
        if err:
            print(f"  ✗ {name}: could not download ({err})")
            missing.append((name, page, dest))

    if missing:
        print("\nDownload these by hand, then run the command again:")
        for name, page, dest in missing:
            print(f"  - {name}: open {page}\n    save the Q{q} {y} industrial PDF as {dest}")
    return not missing


if __name__ == "__main__":
    ok = fetch(sys.argv[1])
    sys.exit(0 if ok else 1)

"""Step 2: pull the numbers out of the PDFs and save them into data/history.json.

- The national report gives one row per metro: inventory, vacancy, absorption, deliveries,
  construction and rent. This goes into each metro's quarterly "series".
- Each city's own report gives its submarket table. This goes into "submarkets".

Claude reads the PDFs. Lessons from building the prototype are written into the prompts:
the tables have several absorption columns (this quarter, earlier quarters, year to date),
and it's easy to grab the wrong one, so the prompt names each column precisely. The checks
in step 3 then catch mistakes that slip through.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import config  # noqa: E402
from scripts.claude_api import ask_structured  # noqa: E402

HISTORY = config.DATA / "history.json"

NATIONAL_SCHEMA = {
    "type": "object",
    "properties": {
        "rows": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "market": {"type": "string", "description": "Market name exactly as printed"},
                    "inv": {"type": "number", "description": "Inventory, sf"},
                    "del_ytd": {"type": "number", "description": "Deliveries / completions year to date, sf"},
                    "uc": {"type": "number", "description": "Under construction, sf"},
                    "vac": {"type": "number", "description": "Overall vacancy rate for THIS quarter, percent (e.g. 8.8)"},
                    "abs_q": {"type": "number", "description": "Overall net absorption for THIS quarter only, sf (negative if in parentheses)"},
                    "abs_ytd": {"type": ["number", "null"], "description": "Overall net absorption year to date, sf, or null if the table has no YTD column"},
                    "rent": {"type": "number", "description": "Overall weighted average asking rent for THIS quarter, all product types, $/sf/yr"},
                },
                "required": ["market", "inv", "del_ytd", "uc", "vac", "abs_q", "rent"],
            },
        },
        "us_vacancy": {"type": "number", "description": "United States total overall vacancy rate this quarter, percent"},
    },
    "required": ["rows", "us_vacancy"],
}

LOCAL_SCHEMA = {
    "type": "object",
    "properties": {
        "rent_basis": {"type": "string", "description": "How the report quotes rent, e.g. 'monthly NNN' or 'annual net, warehouse/distribution'"},
        "submarkets": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "inv": {"type": "number", "description": "Inventory, sf"},
                    "vac": {"type": "number", "description": "Overall vacancy rate, percent"},
                    "abs_ytd": {"type": ["number", "null"], "description": "Net absorption YEAR TO DATE, sf (not this quarter)"},
                    "uc": {"type": ["number", "null"], "description": "Under construction, sf"},
                    "rent": {"type": ["number", "null"], "description": "Overall asking rent converted to $/sf/YEAR (multiply monthly figures by 12)"},
                    "rent_note": {"type": ["string", "null"], "description": "'MF' if this row's rent is a manufacturing rent, else null"},
                },
                "required": ["name", "inv", "vac"],
            },
        },
        "total": {
            "type": "object",
            "description": "The market TOTAL row of the same table",
            "properties": {"inv": {"type": "number"}, "vac": {"type": "number"}, "abs_ytd": {"type": ["number", "null"]}, "uc": {"type": ["number", "null"]}},
            "required": ["inv", "vac"],
        },
    },
    "required": ["rent_basis", "submarkets", "total"],
}


def load():
    return json.loads(HISTORY.read_text())


def save(h):
    HISTORY.write_text(json.dumps(h, indent=1, ensure_ascii=False))


def extract_national(quarter, h):
    y, q = config.parse_quarter(quarter)
    pdf = config.RAW / quarter / "national.pdf"
    names = [m["national_row"] for m in config.METROS.values()]
    prompt = (
        f"This is Cushman & Wakefield's U.S. Industrial MarketBeat for Q{q} {y}. "
        f"Find the market statistics table(s) and return the rows for exactly these markets: {names}. "
        "The table has SEVERAL net absorption columns (this quarter, earlier quarters, and year to date). "
        f"abs_q must come from the column for Q{q} {y} only; abs_ytd from the year-to-date column. "
        f"vac and rent must be the Q{q} {y} columns, not earlier quarters. Rent must be the 'overall / all product types' "
        "asking rent in $/sf per year. Numbers in parentheses are negative. Copy numbers exactly; do not estimate."
    )
    out = ask_structured(prompt, NATIONAL_SCHEMA, "record_national_rows", pdf_path=pdf)
    by_name = {r["market"].strip().lower(): r for r in out["rows"]}
    for mid, m in config.METROS.items():
        row = by_name.get(m["national_row"].lower())
        if row is None:  # loose match
            row = next((r for k, r in by_name.items() if m["national_row"].split(",")[0].lower() in k), None)
        if row is None:
            print(f"  ✗ {mid}: row '{m['national_row']}' not found in national table")
            continue
        clean = {k: row.get(k) for k in ["rent", "vac", "abs_q", "del_ytd", "inv", "uc", "abs_ytd"] if row.get(k) is not None}
        h["metros"].setdefault(mid, {"name_en": m["name_en"], "name_zh": m["name_zh"], "series": {}, "submarkets": {}})
        h["metros"][mid]["series"][quarter] = clean
        print(f"  ✓ {mid}: vacancy {clean['vac']}%, rent ${clean['rent']}, absorption {clean['abs_q']:,.0f} sf")
    h.setdefault("us_vacancy", {})[quarter] = out["us_vacancy"]
    if quarter not in h["quarters"]:
        h["quarters"].append(quarter)
        h["quarters"].sort(key=config.parse_quarter)


def extract_local(quarter, mid, h):
    pdf = config.RAW / quarter / f"{mid}.pdf"
    if not pdf.exists():
        print(f"  – {mid}: no local report, keeping last quarter's submarkets")
        return
    y, q = config.parse_quarter(quarter)
    prompt = (
        f"This is Cushman & Wakefield's {config.METROS[mid]['name_en']} industrial MarketBeat for Q{q} {y}. "
        "Return every row of the submarket statistics table, plus the market total row. "
        "abs_ytd must be YEAR-TO-DATE net absorption, not the current quarter. "
        "Convert rents quoted per month to per year by multiplying by 12. If the table shows separate "
        "manufacturing and warehouse rents, use the overall/all rent if there is one, otherwise warehouse/distribution, "
        "and set rent_note to 'MF' only when the only rent given for that row is manufacturing. "
        "If the report splits the metro into sub-regions with their own subtotals (e.g. Dallas and Fort Worth), return only "
        "the individual submarkets, not the subtotals. Copy numbers exactly."
    )
    out = ask_structured(prompt, LOCAL_SCHEMA, "record_submarkets", pdf_path=pdf)
    subs = [{k: s.get(k) for k in ["name", "inv", "vac", "abs_ytd", "uc", "rent", "rent_note"] if k != "rent_note" or s.get(k)} for s in out["submarkets"]]
    subs.sort(key=lambda s: -s["inv"])
    h["metros"][mid]["submarkets"][quarter] = subs
    h["metros"][mid].setdefault("local_totals", {})[quarter] = out["total"]
    h["metros"][mid].setdefault("rent_basis", {})[quarter] = out["rent_basis"]
    print(f"  ✓ {mid}: {len(subs)} submarkets")


def run(quarter):
    h = load()
    print("Reading the national report…")
    extract_national(quarter, h)
    print("Reading the city reports…")
    for mid in config.METROS:
        try:
            extract_local(quarter, mid, h)
        except Exception as e:  # keep going; the check step will point out what's missing
            print(f"  ✗ {mid}: {e}")
    save(h)


if __name__ == "__main__":
    run(sys.argv[1])

"""Step 4: have Claude write each city's "market update".

Only the numbers from data/history.json go into the prompt, so the summary can't
invent figures. Results are saved to data/notes.json.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import config  # noqa: E402
from scripts.claude_api import ask_structured  # noqa: E402

NOTES = config.DATA / "notes.json"
HISTORY = config.DATA / "history.json"

SCHEMA = {
    "type": "object",
    "properties": {
        "en": {"type": "string", "description": "English paragraph, 70-110 words"},
    },
    "required": ["en"],
}

STYLE = """Write a short quarterly market update for an industrial real estate market, for REIT investors.
Rules:
- One paragraph, 70-110 words. Plain, factual language, like a research analyst.
- Cover: occupancy and its change, net absorption this quarter, asking rent and its change (quarter over quarter,
  and vs a year ago or vs the oldest quarter shown), new supply and construction pipeline, the strongest and weakest
  submarkets. End with one sentence on what to watch.
- Use only the numbers given. Do not invent figures, tenant names or causes that aren't in the data.
- Occupancy = 100 - vacancy. Use M sf with 1-2 decimals. Rents in $/sf/yr.
Example of the tone (Los Angeles, Q2 2026):
"In Q2 2026, Los Angeles occupancy rose to 95.8%, up 0.4 points from Q1, as tenants absorbed a net 1.23M sf, led by
LA South (+1.98M sf in the quarter). Asking rents slipped to $15.83/sf/yr, down 1.4% QoQ and 8.3% below Q3 2024.
New supply is thin: 0.76M sf delivered this year and 4.4M sf under construction, about 0.6% of stock. With little new
space coming, occupancy should stay tight, and rents look more likely to stabilize than to rebound soon."
"""


def facts(h, mid, quarter):
    m = h["metros"][mid]
    qs = [k for k in h["quarters"] if k in m["series"]]
    qs = qs[qs.index(quarter) - config.WINDOW + 1: qs.index(quarter) + 1] if quarter in qs else qs[-config.WINDOW:]
    rows = [{"quarter": config.qlabel(k), **m["series"][k]} for k in qs]
    subs = m.get("submarkets", {}).get(quarter) or []
    return {"metro": m["name_en"], "latest_quarter": config.qlabel(quarter), "history_oldest_to_latest": rows, "submarkets_latest": subs}


def run(quarter, only=None):
    h = json.loads(HISTORY.read_text())
    notes = json.loads(NOTES.read_text()) if NOTES.exists() else {}
    for mid in h["metros"]:
        if only and mid != only:
            continue
        if quarter not in h["metros"][mid]["series"]:
            continue
        data = json.dumps(facts(h, mid, quarter), ensure_ascii=False)
        out = ask_structured(STYLE + "\n\nData (JSON):\n" + data, SCHEMA, "write_update", max_tokens=2000)
        notes.setdefault(mid, {})[quarter] = out
        print(f"  ✓ {mid}: {out['en'][:80]}…")
    NOTES.write_text(json.dumps(notes, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    run(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)

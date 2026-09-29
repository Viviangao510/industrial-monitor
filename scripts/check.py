"""Step 3: check the numbers before they go on the dashboard.

Writes a plain-English list of problems to data/checks/<quarter>.txt and prints it.
It also hides submarket columns that don't add up to the city total, so a bad
extraction never shows up on the page as if it were real.

Checks:
  1. Submarkets add up to the city total (size, vacancy, absorption, construction).
  2. Big jumps from last quarter (vacancy moves 2+ points, rent moves 10%+) that might be a misread.
  3. This year's quarterly absorption adds up to the year-to-date figure (differences usually mean
     Cushman revised an earlier quarter, which is normal, but worth knowing).
  4. Required numbers are present for every city.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import config  # noqa: E402

HISTORY = config.DATA / "history.json"


def _close(a, b, tol):
    return b != 0 and abs(a - b) / abs(b) <= tol


def run(quarter, apply=True):
    h = json.loads(HISTORY.read_text())
    issues, notes = [], []
    prev = config.prev_quarter(quarter)

    for mid, m in h["metros"].items():
        name = m["name_en"]
        s = m["series"].get(quarter)
        if not s:
            issues.append(f"{name}: no data for {quarter}.")
            continue
        for f in ["rent", "vac", "abs_q", "del_ytd", "inv", "uc"]:
            if s.get(f) is None:
                issues.append(f"{name}: missing '{f}'.")

        # 2. big jumps
        p = m["series"].get(prev)
        if p:
            if abs(s["vac"] - p["vac"]) >= 2:
                issues.append(f"{name}: vacancy moved from {p['vac']}% to {s['vac']}% in one quarter. Check the PDF.")
            if abs(s["rent"] / p["rent"] - 1) >= 0.10:
                issues.append(f"{name}: rent moved from ${p['rent']} to ${s['rent']} in one quarter. Check the PDF.")

        # 3. quarterly absorption vs YTD
        y, q = config.parse_quarter(quarter)
        if s.get("abs_ytd") is not None and q > 1:
            qs = [config.qkey(y, i) for i in range(1, q + 1)]
            if all(k in m["series"] for k in qs):
                total = sum(m["series"][k]["abs_q"] for k in qs)
                if not _close(total, s["abs_ytd"], 0.05):
                    notes.append(f"{name}: this year's quarters add up to {total:,.0f} sf but year to date is {s['abs_ytd']:,.0f} sf. "
                                 "Cushman probably revised an earlier quarter; the charts show quarters as first reported.")

        # 1. submarkets vs total
        subs = m.get("submarkets", {}).get(quarter)
        if subs:
            inv = sum(x["inv"] for x in subs)
            if not _close(inv, s["inv"], 0.02):
                issues.append(f"{name}: submarkets add up to {inv/1e6:.1f}M sf but the city total is {s['inv']/1e6:.1f}M sf.")
            wvac = sum(x["inv"] * x["vac"] for x in subs) / inv
            if abs(wvac - s["vac"]) > 0.3:
                issues.append(f"{name}: submarket vacancy averages {wvac:.1f}% vs city {s['vac']}%.")
            hidden = []
            local_total = m.get("local_totals", {}).get(quarter, {})
            for col in ["abs_ytd", "uc"]:
                vals = [x.get(col) for x in subs]
                if any(v is None for v in vals):
                    continue
                target = local_total.get(col) if local_total.get(col) is not None else s.get(col)
                if target is None:
                    continue
                tot = sum(vals)
                ok = _close(tot, target, 0.05) or abs(tot - target) < 50_000
                if not ok:
                    hidden.append(col)
                    issues.append(f"{name}: submarket '{col}' adds up to {tot:,.0f} but the total is {target:,.0f}. Column hidden on the dashboard.")
            if apply and hidden:
                for x in subs:
                    for col in hidden:
                        x[col] = None
                m["partial_submarkets"] = True
        else:
            notes.append(f"{name}: no submarket table for {quarter}; the dashboard keeps the latest one it has.")

    config.CHECKS.mkdir(parents=True, exist_ok=True)
    lines = [f"Checks for {quarter}", ""]
    lines += ["PROBLEMS (look at these before publishing):"] + ([f"  - {i}" for i in issues] or ["  none"])
    lines += ["", "NOTES (usually fine):"] + ([f"  - {n}" for n in notes] or ["  none"])
    text = "\n".join(lines)
    (config.CHECKS / f"{quarter}.txt").write_text(text)
    print(text)
    if apply:
        HISTORY.write_text(json.dumps(h, indent=1, ensure_ascii=False))
    return issues


if __name__ == "__main__":
    run(sys.argv[1])

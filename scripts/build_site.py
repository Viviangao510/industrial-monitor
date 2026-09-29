"""Step 5: build the dashboard page from the data files.

Reads data/history.json and data/notes.json, puts the numbers into site/template.html,
and writes site/index.html: one self-contained file you can double-click to open.
"""
import datetime as dt
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import config  # noqa: E402


def build(latest=None):
    h = json.loads((config.DATA / "history.json").read_text())
    notes = json.loads((config.DATA / "notes.json").read_text())
    all_q = sorted(h["quarters"], key=config.parse_quarter)
    latest = latest or all_q[-1]
    window = all_q[: all_q.index(latest) + 1][-config.WINDOW:]

    metros = []
    for mid, m in h["metros"].items():
        s = m["series"]
        if latest not in s:
            print(f"  – {mid}: no {latest} data, left out")
            continue

        def arr(f):
            return [s.get(q, {}).get(f) for q in window]

        # quarterly deliveries from year-to-date totals
        dels = []
        for q in window:
            y, n = config.parse_quarter(q)
            cur = s.get(q, {}).get("del_ytd")
            prev = s.get(config.prev_quarter(q), {}).get("del_ytd") if n > 1 else 0
            dels.append(None if cur is None or prev is None else cur - prev)

        cur, prev_q = s[latest], s.get(window[-2], {})
        y, n = config.parse_quarter(latest)
        abs_ytd = cur.get("abs_ytd")
        if abs_ytd is None:
            qs = [config.qkey(y, i) for i in range(1, n + 1)]
            abs_ytd = sum(s[k]["abs_q"] for k in qs) if all(k in s for k in qs) else cur["abs_q"]
        same_last_year = s.get(config.prev_quarter(latest, 4), {})

        sub_q = latest if latest in m.get("submarkets", {}) else max(m.get("submarkets", {}) or [latest], key=config.parse_quarter)
        subs = [[x["name"], x["inv"], x["vac"], x.get("abs_ytd"), x.get("uc"), x.get("rent")] + ([x["rent_note"]] if x.get("rent_note") else [])
                for x in m.get("submarkets", {}).get(sub_q, [])]

        note = notes.get(mid, {}).get(latest) or {"en": "No market update written for this quarter yet.", "zh": "本季度市场动态尚未生成。"}
        metros.append({
            "id": mid, "en": m["name_en"], "zh": m["name_zh"],
            "rent": arr("rent"), "vac": arr("vac"), "abs": arr("abs_q"), "del": dels,
            "inv": cur["inv"], "invPrev": prev_q.get("inv", cur["inv"]),
            "uc": cur["uc"], "ucPrev": prev_q.get("uc", cur["uc"]),
            "ytdAbs": abs_ytd, "ytdDel": cur["del_ytd"], "prevYtdDel": same_last_year.get("del_ytd") or cur["del_ytd"],
            "partial": bool(m.get("partial_submarkets")), "subs": subs, "note": note,
        })

    data = {
        "quarters": [config.qlabel(q) for q in window],
        "metros": metros,
        "meta": {
            "period": f"{config.parse_quarter(latest)[0]}-Q{config.parse_quarter(latest)[1]}",
            "generated": dt.date.today().isoformat(),
            "us_vac": h.get("us_vacancy", {}).get(latest, config.US_VACANCY_DEFAULT),
        },
    }
    tpl = (config.SITE / "template.html").read_text()
    tpl = tpl.replace("/*__DATA__*/null", json.dumps(data, ensure_ascii=False))
    head, body = tpl.split('<div class="app">', 1)
    html = ('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
            + head + '</head>\n<body>\n<div class="app">' + body + '\n</body>\n</html>\n')
    out = config.SITE / "index.html"
    out.write_text(html)
    print(f"  ✓ built {out} ({len(metros)} metros, {window[0]}–{window[-1]})")
    return out


if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else None)

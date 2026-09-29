# Industrial Market Monitor

A dashboard for REIT investors that tracks the industrial (warehouse) real estate market in five US metros and their submarkets: Los Angeles, Inland Empire, Dallas–Fort Worth, Chicago and Northern New Jersey.

Every quarter, one command downloads the new Cushman & Wakefield reports, has Claude read the numbers out of the PDFs, checks them, has Claude write a short market update for each city (English and Chinese), and rebuilds the dashboard.

## What's in this folder

| Path | What it is |
|---|---|
| `run_quarter.py` | The one command you run each quarter |
| `config.py` | Settings: which metros, report links, which Claude model |
| `scripts/fetch_reports.py` | Step 1: downloads the PDF reports |
| `scripts/extract.py` | Step 2: Claude reads the PDFs; numbers are saved to `data/history.json` |
| `scripts/check.py` | Step 3: checks the numbers and lists problems in `data/checks/` |
| `scripts/summarize.py` | Step 4: Claude writes each city's market update into `data/notes.json` |
| `scripts/build_site.py` | Step 5: builds `site/index.html` from the data |
| `data/history.json` | All the numbers, quarter by quarter (starts with Q3 2024 – Q2 2026) |
| `data/notes.json` | The written market updates |
| `data/raw/` | Downloaded PDFs, one folder per quarter |
| `site/template.html` | The dashboard design (charts, layout, English/Chinese text) |
| `site/index.html` | The finished dashboard; double-click to open |

## One-time setup

1. **Python.** On a Mac, open Terminal and type `python3 --version`. If you see a version number (3.10 or newer), you're set. If not, install it from python.org.
2. **Install the two libraries this project uses.** In Terminal, go to this folder and run:
   ```
   cd ~/Documents/industrial-monitor
   python3 -m pip install -r requirements.txt
   ```
3. **Add your Claude API key.** Get one at console.anthropic.com (API keys). Copy `.env.example` to a new file called `.env` and paste your key after `ANTHROPIC_API_KEY=`. The `.env` file stays on your computer and is never shared.

## First: test it (once)

```
python3 test_extraction.py
```

This has Claude re-read the Q2 2026 reports and compares every number with the ones already checked by hand. It doesn't change your data. If most numbers match, the pipeline is ready.

## Each quarter

Cushman usually publishes new reports 2–4 weeks after a quarter ends (Q3 reports arrive around mid-to-late October).

```
python3 run_quarter.py 2026Q3
```

Then:
1. Read `data/checks/2026Q3.txt`. "Problems" are things to look at in the PDF before sharing; "Notes" are usually fine.
2. Open `site/index.html` to see the updated dashboard.

If a report won't download, the script tells you which page to download it from by hand and exactly what to name the file. Save it there and run the same command again with `--skip-fetch`.

To rebuild the page without calling Claude (for example, after you edit the design):
```
python3 run_quarter.py --build-only
```

## Using Claude Code instead of typing commands

Open this folder in Claude Code (in the Claude desktop app, or by typing `claude` in Terminal inside this folder) and ask in plain English, for example:

- "Run the quarterly update for 2026Q3 and tell me what the checks found."
- "Add Atlanta as a sixth metro."
- "Add a chart of construction pipeline by submarket."

Claude Code reads `CLAUDE.md` first, so it already knows how the project works.

## Costs

Each quarterly run makes about 11 Claude API calls (6 PDFs to read, 5 summaries). That's usually well under $1 per quarter.

## Source and caveats

Data: Cushman & Wakefield MarketBeat reports (national industrial tables and local city reports). Cushman revises earlier quarters later; this project keeps each quarter as it was first reported, and the checks point out large revisions. Not investment advice.

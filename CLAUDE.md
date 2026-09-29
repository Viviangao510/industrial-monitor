# Industrial Market Monitor — notes for Claude Code

## What this is
A quarterly dashboard of US industrial real estate market health (5 metros + submarkets) for REIT investors. Owner: Vivian, who is not a programmer. Explain what you're doing in plain language, avoid jargon, and ask before changing the dashboard design.

## Framework the dashboard follows
Demand vs supply decides the direction of vacancy, which decides the direction of rent:
- Demand: net absorption
- Supply: deliveries and space under construction
- Balance: vacancy / occupancy (occupancy = 100 − vacancy)
- Price: asking rent and its change (QoQ, YoY)
Each metro gets a "market read" (Strong / Mixed / Weak) from four checks in `site/template.html` → `read()`: vacancy vs US, YTD absorption vs deliveries, rent YoY, construction as % of stock.

## Pipeline (`python3 run_quarter.py 2026Q3`)
1. `scripts/fetch_reports.py` → `data/raw/<Q>/national.pdf` and `<metro>.pdf`
2. `scripts/extract.py` → Claude reads PDFs via the API (tool use for strict JSON) → `data/history.json`
3. `scripts/check.py` → `data/checks/<Q>.txt`; hides submarket columns that don't reconcile
4. `scripts/summarize.py` → Claude writes each metro's update (English only) → `data/notes.json`
5. `scripts/build_site.py` → injects data into `site/template.html` → `site/index.html`

## Data rules
- One source only: Cushman & Wakefield, so definitions stay consistent.
- Metro-level series come from the national MarketBeat table; submarkets from each city's local MarketBeat.
- Rents are $/sf/yr. Local reports quoting monthly rents are multiplied by 12.
- Quarters are stored as first reported. Don't overwrite earlier quarters with revised figures unless Vivian asks.
- The national table has several absorption columns; `abs_q` must be the current quarter, `abs_ytd` year to date. This was the most common extraction mistake when building the prototype.
- Never invent numbers. If a figure is missing, leave it null and let the page show "n/a".

## Keys and files
- API key lives in `.env` (ANTHROPIC_API_KEY). Never print it or commit it.
- Model is set in `config.py` (`MODEL`).
- `site/index.html` is generated; edit `site/template.html` instead.

## Confidentiality
The dashboard layout was inspired by an internal tool at a previous employer. Do not add that company's name, branding, screenshots or data to this project.

## Planned next
REIT exposure page (link each REIT's % of rent by metro from its supplemental report to these markets), lease expiry watch, data centers as a second asset class.

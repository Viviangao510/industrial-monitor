"""Settings for the Industrial Market Monitor.

Edit this file to add a metro, change the AI model, or fix a report URL.
"""
from pathlib import Path

ROOT = Path(__file__).parent
DATA = ROOT / "data"
RAW = DATA / "raw"          # downloaded PDF reports, one folder per quarter (e.g. data/raw/2026Q3/)
CHECKS = DATA / "checks"    # check results, one text file per quarter
SITE = ROOT / "site"

# Claude model used for reading PDFs and writing summaries
MODEL = "claude-sonnet-5"

# How many quarters of history the dashboard shows
WINDOW = 8

# US national vacancy used as the benchmark in the "market read" (update each quarter if you like)
US_VACANCY_DEFAULT = 6.9

# Each metro:
#   national_row  - how the metro's row is labelled in Cushman's national table
#   local_urls    - URL patterns for the city's own MarketBeat PDF (submarket table).
#                   {y} = year (2026), {q} = quarter number (3). The first one that downloads is used.
#   local_page    - the web page to download the PDF from by hand if the patterns stop working
METROS = {
    "la": {
        "name_en": "Los Angeles", "name_zh": "洛杉矶",
        "national_row": "Los Angeles, CA",
        "local_urls": [
            "https://assets.cushmanwakefield.com/-/media/cw/marketbeat-pdfs/{y}/q{q}/us-reports/industrial/la_americas_marketbeat_industrial_q{q}-{y}.pdf",
        ],
        "local_page": "https://www.cushmanwakefield.com/en/united-states/insights/us-marketbeats/los-angeles-marketbeats",
    },
    "ie": {
        "name_en": "Inland Empire", "name_zh": "内陆帝国",
        "national_row": "Inland Empire, CA",
        "local_urls": [
            "https://assets.cushmanwakefield.com/-/media/cw/marketbeat-pdfs/{y}/q{q}/us-reports/industrial/inland-empire_americas_marketbeat_industrial_q{q}-{y}.pdf",
        ],
        "local_page": "https://www.cushmanwakefield.com/en/united-states/insights/us-marketbeats/inland-empire-marketbeats",
    },
    "dfw": {
        "name_en": "Dallas–Fort Worth", "name_zh": "达拉斯–沃斯堡",
        "national_row": "Dallas/Ft. Worth, TX",
        "local_urls": [
            "https://assets.cushmanwakefield.com/-/media/cw/marketbeat-pdfs/{y}/q{q}/us-reports/industrial/dallas-fort-worth_americas_marketbeat_industrial_q{q}-{y}.pdf",
        ],
        "local_page": "https://www.cushmanwakefield.com/en/united-states/insights/us-marketbeats/dallas-ft-worth-marketbeats/industrial",
    },
    "chi": {
        "name_en": "Chicago", "name_zh": "芝加哥",
        "national_row": "Chicago, IL",
        "local_urls": [
            "https://assets.cushmanwakefield.com/-/media/cw/marketbeat-pdfs/{y}/q{q}/us-reports/industrial/chicago_americas_marketbeat_industrial_q{q}-{y}.pdf",
        ],
        "local_page": "https://www.cushmanwakefield.com/en/united-states/insights/us-marketbeats/chicago-marketbeats/industrial",
    },
    "nnj": {
        "name_en": "Northern New Jersey", "name_zh": "北新泽西",
        "national_row": "New Jersey - Northern",
        "local_urls": [
            "https://assets.cushmanwakefield.com/-/media/cw/marketbeat-pdfs/{y}/q{q}/us-reports/industrial/nj_americas_marketbeat_industrial_q{q}{y}.pdf",
        ],
        "local_page": "https://www.cushmanwakefield.com/en/united-states/insights/us-marketbeats/new-jersey-marketbeats",
    },
}

# Exact links for reports whose file names don't follow a pattern (add new ones here if a download fails)
KNOWN_URLS = {
    "2026Q2": {
        "dfw": "https://content.cushmanwakefield.com/api/public/content/d5ef82ed60004f66912bd4c3e2fc5666?v=f2b072d1",
        "chi": "https://content.cushmanwakefield.com/api/public/content/fa0b11d15a7145efbba3315b1955e399?v=1c16dde9",
    },
}

NATIONAL_URL = "https://assets.cushmanwakefield.com/-/media/cw/marketbeat-pdfs/{y}/q{q}/us-reports/national/q{q}{y}usindustrialmarketbeat.pdf"
NATIONAL_PAGE = "https://www.cushmanwakefield.com/en/united-states/insights/us-marketbeats/us-industrial-marketbeat"


def parse_quarter(text):
    """'2026Q3' or '2026-Q3' -> (2026, 3)"""
    t = text.upper().replace("-", "").replace(" ", "")
    y, q = t.split("Q")
    return int(y), int(q)


def qkey(y, q):
    return f"{y}Q{q}"


def qlabel(key):
    """'2026Q3' -> "Q3'26" (the label shown on charts)"""
    y, q = parse_quarter(key)
    return f"Q{q}'{str(y)[2:]}"


def prev_quarter(key, n=1):
    y, q = parse_quarter(key)
    for _ in range(n):
        q -= 1
        if q == 0:
            y, q = y - 1, 4
    return qkey(y, q)

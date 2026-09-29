"""Small helper for calling Claude with a PDF (or text) and getting structured data back.

Uses "tool use" so Claude must answer in the exact JSON shape we ask for.
Needs ANTHROPIC_API_KEY in your environment (or in a .env file in the project folder).
"""
import base64
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import config  # noqa: E402


def _load_env():
    txt = config.ROOT / "API_KEY.txt"
    if txt.exists() and not os.environ.get("ANTHROPIC_API_KEY"):
        for line in txt.read_text().splitlines():
            line = line.strip()
            if line.startswith("sk-"):
                os.environ["ANTHROPIC_API_KEY"] = line
    env = config.ROOT / ".env"
    if env.exists():
        for line in env.read_text().splitlines():
            if "=" in line and not line.strip().startswith("#"):
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"'))


def client():
    _load_env()
    if not os.environ.get("ANTHROPIC_API_KEY"):
        sys.exit("No API key found. Open API_KEY.txt in the project folder, paste your key on its own line, and save.")
    import anthropic
    return anthropic.Anthropic()


def ask_structured(prompt, schema, tool_name, pdf_path=None, max_tokens=8000):
    """Send a prompt (plus an optional PDF) and return the dict Claude fills in for `schema`."""
    content = []
    if pdf_path:
        data = base64.standard_b64encode(Path(pdf_path).read_bytes()).decode()
        content.append({"type": "document", "source": {"type": "base64", "media_type": "application/pdf", "data": data}})
    content.append({"type": "text", "text": prompt})
    resp = client().messages.create(
        model=config.MODEL,
        max_tokens=max_tokens,
        tools=[{"name": tool_name, "description": "Record the requested data.", "input_schema": schema}],
        tool_choice={"type": "tool", "name": tool_name},
        messages=[{"role": "user", "content": content}],
    )
    for block in resp.content:
        if block.type == "tool_use":
            return block.input
    raise RuntimeError("Claude did not return structured data")

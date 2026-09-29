# Putting this project on GitHub (instructions for Claude Code)

Goal: a public GitHub repo named `industrial-monitor`, the dashboard live on GitHub Pages, and the quarterly update running automatically.

1. Make sure the GitHub CLI (`gh`) is installed (`brew install gh` if Homebrew is available) and the user is logged in (`gh auth login`, browser flow — let the user click through it).
2. Move `update-and-publish.yml` from the project root into `.github/workflows/` (create the folders).
3. In this folder: `git init`, commit everything. Confirm `API_KEY.txt`, `.env` and `data/raw/` are NOT committed (they're in .gitignore).
4. `gh repo create industrial-monitor --public --source . --push`
5. Add the API key as a repository secret without printing it:
   `grep '^sk-' API_KEY.txt | head -1 | gh secret set ANTHROPIC_API_KEY`
6. Turn on GitHub Pages with GitHub Actions as the source:
   `gh api -X POST repos/{owner}/industrial-monitor/pages -f build_type=workflow`
7. Run the workflow once: `gh workflow run "Update and publish"`, wait for it (`gh run watch`), and give the user the site link (https://<username>.github.io/industrial-monitor/).
8. Explain in plain words: the site updates itself each quarter; if an update fails, GitHub emails them; check results are in `data/checks/`.

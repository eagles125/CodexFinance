# CodexFinance

CodexFinance is a local Codex setup for A-share and Hong Kong equity research. It contains:

- A Codex skill: `equity-research-assistant`
- A local MCP server: `codex-finance`
- Local folders for notes, data, filings, and reports
- Config templates suitable for GitHub version control

This project is for research assistance only. It does not provide personalized financial advice or automated trading instructions.

## Layout

```text
skills/equity-research-assistant/
mcp/codex-finance-mcp/
data/
notes/
configs/
scripts/
```

## Local Setup

Install Python dependencies:

```powershell
cd E:\ai\CodexFinance\mcp\codex-finance-mcp
python -m pip install -r requirements.txt
```

Register the MCP server and skill path in your Codex config. See `configs/codex-config-snippet.toml`.

## GitHub

Initialize and push:

```powershell
cd E:\ai\CodexFinance
git init
git add .
git commit -m "Initial CodexFinance setup"
git branch -M main
git remote add origin https://github.com/<your-user>/CodexFinance.git
git push -u origin main
```

Do not commit `.env`, local databases, downloaded reports, or private notes unless you intentionally want them in the repository.

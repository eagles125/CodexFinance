$ErrorActionPreference = "Stop"

Write-Host "CodexFinance setup check"
Write-Host "Home: E:\ai\CodexFinance"

python --version
python -m pip show mcp akshare pandas python-dotenv | Out-Host

$env:CODEX_FINANCE_HOME = "E:\ai\CodexFinance"
@"
import importlib.util

path = r"E:\ai\CodexFinance\mcp\codex-finance-mcp\server.py"
spec = importlib.util.spec_from_file_location("codex_finance_server", path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
print(module.data_source_status())
"@ | python -

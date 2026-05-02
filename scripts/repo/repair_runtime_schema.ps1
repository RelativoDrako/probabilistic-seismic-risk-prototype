[CmdletBinding()]
param(
    [string]$RepoRoot = "."
)

$ErrorActionPreference = "Stop"

$repoRootPath = (Resolve-Path -LiteralPath $RepoRoot).Path
$venvPython = Join-Path $repoRootPath ".venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $venvPython)) {
    $venvPython = Join-Path $repoRootPath "venv\Scripts\python.exe"
}
$pythonExe = if (Test-Path -LiteralPath $venvPython) { $venvPython } else { "python" }

$code = @'
import sys
from pathlib import Path

repo = Path(sys.argv[1]).resolve()
if str(repo) not in sys.path:
    sys.path.insert(0, str(repo))

from src.common.settings import get_settings
from src.common.schema import create_schema

settings = get_settings(repo)
db_path = create_schema(settings.sqlite_path)

print("[repair_runtime_schema] ok")
print(f"[repair_runtime_schema] db_path={db_path}")
'@

$tempPy = Join-Path $repoRootPath "artifacts\reports\_tmp_repair_runtime_schema.py"
$tempDir = Split-Path -Parent $tempPy
if (-not (Test-Path -LiteralPath $tempDir)) {
    New-Item -ItemType Directory -Path $tempDir -Force | Out-Null
}
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText($tempPy, $code, $utf8NoBom)

Push-Location $repoRootPath
try {
    & $pythonExe $tempPy $repoRootPath
    if ($LASTEXITCODE -ne 0) {
        throw "Runtime schema repair failed with exit code $LASTEXITCODE"
    }
}
finally {
    Pop-Location
    if (Test-Path -LiteralPath $tempPy) {
        Remove-Item -LiteralPath $tempPy -Force -ErrorAction SilentlyContinue
    }
}

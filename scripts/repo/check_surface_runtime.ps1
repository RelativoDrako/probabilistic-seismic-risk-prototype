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

$reportsDir = Join-Path $repoRootPath "artifacts\reports"
if (-not (Test-Path -LiteralPath $reportsDir)) {
    New-Item -ItemType Directory -Path $reportsDir -Force | Out-Null
}

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$tempPy = Join-Path $reportsDir "_tmp_check_surface_runtime.py"
$logPath = Join-Path $reportsDir ("check_surface_runtime_{0}.log" -f $timestamp)

$code = @'
import sys
import traceback
from pathlib import Path

repo_root = Path(sys.argv[1]).resolve()

if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

print(f"[check_surface_runtime] repo_root={repo_root}")
print(f"[check_surface_runtime] python={sys.executable}")

def checkpoint(name: str) -> None:
    print(f"[check_surface_runtime] checkpoint={name}")

try:
    checkpoint("import_settings")
    from src.common.settings import get_settings

    checkpoint("import_sqlite")
    from src.common.sqlite import managed_connection, transaction

    checkpoint("import_schema")
    from src.common.schema import create_schema

    checkpoint("import_api_repository")
    from src.api.repository import get_latest_summary, get_latest_evaluation

    checkpoint("load_settings")
    settings = get_settings(repo_root)
    print(f"[check_surface_runtime] sqlite_path={settings.sqlite_path}")

    checkpoint("create_schema")
    db_path = create_schema(settings.sqlite_path)
    print(f"[check_surface_runtime] db_path={db_path}")

    checkpoint("connection")
    with managed_connection(db_path) as connection:
        with transaction(connection):
            connection.execute("SELECT 1")

    checkpoint("summary")
    summary = get_latest_summary(db_path)
    print(f"[check_surface_runtime] latest_feature_generation_present={summary.get('latest_feature_generation') is not None}")

    checkpoint("evaluation")
    evaluation = get_latest_evaluation(db_path)
    print(f"[check_surface_runtime] latest_evaluation_present={evaluation.get('evaluation_report_id') is not None}")

    print("[check_surface_runtime] ok")
except Exception:
    print("[check_surface_runtime] failed")
    traceback.print_exc()
    sys.exit(1)
'@

$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText($tempPy, $code, $utf8NoBom)

Push-Location $repoRootPath
try {
    $oldPyPath = $env:PYTHONPATH
    if ([string]::IsNullOrWhiteSpace($oldPyPath)) {
        $env:PYTHONPATH = $repoRootPath
    } else {
        $env:PYTHONPATH = "$repoRootPath;$oldPyPath"
    }

    # ✅ capturar salida correctamente
    $output = & $pythonExe $tempPy $repoRootPath 2>&1
    $exitCode = $LASTEXITCODE

    # ✅ mostrar y guardar log
    $output | Tee-Object -FilePath $logPath

    Write-Host ("[check_surface_runtime] log={0}" -f $logPath)

    if ($exitCode -ne 0) {
        throw "Runtime check failed with exit code $exitCode"
    }
}
finally {
    if ($null -eq $oldPyPath) {
        Remove-Item Env:PYTHONPATH -ErrorAction SilentlyContinue
    } else {
        $env:PYTHONPATH = $oldPyPath
    }

    Pop-Location
    if (Test-Path -LiteralPath $tempPy) {
        Remove-Item -LiteralPath $tempPy -Force -ErrorAction SilentlyContinue
    }
}
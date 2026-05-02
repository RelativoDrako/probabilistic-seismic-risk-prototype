param(
    [Parameter(Mandatory = $true)]
    [string]$RepoRoot
)

$ErrorActionPreference = "Stop"

$target = Join-Path $RepoRoot "src\ingestion\manifest_service.py"
if (!(Test-Path $target)) {
    throw "No existe: $target"
}

$backupRoot = Join-Path $RepoRoot "_ops_backups\ingestion_csv_only_fix"
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backupDir = Join-Path $backupRoot $timestamp
New-Item -ItemType Directory -Force -Path $backupDir | Out-Null
Copy-Item $target (Join-Path $backupDir "manifest_service.py") -Force

$content = Get-Content $target -Raw -Encoding UTF8

if ($content -match "CSV_ONLY_DISCOVERY_GUARD") {
    Write-Host "[skip] manifest_service.py already patched"
    Write-Host "[ok] backup_dir=$backupDir"
    exit 0
}

$patched = $false

# Caso 1: for path in sorted(raw_input_dir.iterdir()):
$pattern1 = '(?ms)(for\s+path\s+in\s+sorted\(\s*raw_input_dir\.iterdir\(\)\s*\)\s*:\s*\r?\n)'
$inject1 = @'
$1        # CSV_ONLY_DISCOVERY_GUARD
        if not path.is_file():
            continue
        if "_meta" in path.parts:
            continue
        if path.suffix.lower() != ".csv":
            continue
'@
$newContent = [regex]::Replace($content, $pattern1, $inject1, 1)
if ($newContent -ne $content) {
    $patched = $true
}

# Caso 2: for p in sorted(raw_input_dir.iterdir()):
if (-not $patched) {
    $pattern2 = '(?ms)(for\s+p\s+in\s+sorted\(\s*raw_input_dir\.iterdir\(\)\s*\)\s*:\s*\r?\n)'
    $inject2 = @'
$1        # CSV_ONLY_DISCOVERY_GUARD
        if not p.is_file():
            continue
        if "_meta" in p.parts:
            continue
        if p.suffix.lower() != ".csv":
            continue
'@
    $newContent = [regex]::Replace($content, $pattern2, $inject2, 1)
    if ($newContent -ne $content) {
        $patched = $true
    }
}

# Caso 3: for path in sorted(raw_input_dir.rglob("*")):
if (-not $patched) {
    $pattern3 = '(?ms)(for\s+path\s+in\s+sorted\(\s*raw_input_dir\.rglob\(\s*["'']\*["'']\s*\)\s*\)\s*:\s*\r?\n)'
    $inject3 = @'
$1        # CSV_ONLY_DISCOVERY_GUARD
        if not path.is_file():
            continue
        if "_meta" in path.parts:
            continue
        if path.suffix.lower() != ".csv":
            continue
'@
    $newContent = [regex]::Replace($content, $pattern3, $inject3, 1)
    if ($newContent -ne $content) {
        $patched = $true
    }
}

if (-not $patched) {
    throw "No se pudo aplicar el parche automáticamente. Revisión manual requerida en manifest_service.py"
}

[System.IO.File]::WriteAllText($target, $newContent, (New-Object System.Text.UTF8Encoding($false)))

Write-Host "[ok] backup_dir=$backupDir"
Write-Host "[ok] patched=$target"
Write-Host "[next] rerun ingest for usgs_mexico_catalog"

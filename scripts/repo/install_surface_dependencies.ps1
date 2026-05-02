[CmdletBinding()]
param(
    [string]$RepoRoot = ".",
    [string]$VenvDir = ".venv",
    [string]$PythonExe = "",
    [switch]$UpgradePip
)

$ErrorActionPreference = "Stop"

$repoRootPath = (Resolve-Path -LiteralPath $RepoRoot).Path
$requirementsPath = Join-Path $repoRootPath "requirements-surface.txt"
if (-not (Test-Path -LiteralPath $requirementsPath)) {
    throw "Missing requirements-surface.txt at $requirementsPath"
}

if ([string]::IsNullOrWhiteSpace($PythonExe)) {
    $pythonCandidates = @("py", "python")
    foreach ($candidate in $pythonCandidates) {
        try {
            & $candidate --version *> $null
            if ($LASTEXITCODE -eq 0) {
                $PythonExe = $candidate
                break
            }
        } catch {
        }
    }
}

if ([string]::IsNullOrWhiteSpace($PythonExe)) {
    throw "No usable Python launcher was found. Install Python 3 and retry."
}

$venvPath = Join-Path $repoRootPath $VenvDir
$venvPython = Join-Path $venvPath "Scripts\python.exe"

if (-not (Test-Path -LiteralPath $venvPython)) {
    Write-Host "[install_surface_dependencies] creating virtual environment..."
    if ($PythonExe -eq "py") {
        & py -3 -m venv $venvPath
    } else {
        & $PythonExe -m venv $venvPath
    }
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to create virtual environment."
    }
}

if (-not (Test-Path -LiteralPath $venvPython)) {
    throw "Virtual environment python not found after creation: $venvPython"
}

if ($UpgradePip) {
    Write-Host "[install_surface_dependencies] upgrading pip..."
    & $venvPython -m pip install --upgrade pip
    if ($LASTEXITCODE -ne 0) { throw "pip upgrade failed." }
}

Write-Host "[install_surface_dependencies] installing surface dependencies..."
& $venvPython -m pip install -r $requirementsPath
if ($LASTEXITCODE -ne 0) {
    throw "Dependency installation failed."
}

Write-Host "[install_surface_dependencies] ok"
Write-Host ("[install_surface_dependencies] venv_python={0}" -f $venvPython)
Write-Host "[install_surface_dependencies] next:"
Write-Host ("powershell -ExecutionPolicy Bypass -File .\scripts\repo\start_presentation_stack.ps1 -RepoRoot `"{0}`"" -f $repoRootPath)

param(
    [string]$PythonExe = "python",
    [switch]$ForceRecreate = $false
)

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Resolve-Path (Join-Path $ScriptDir "..")

Push-Location $ProjectRoot
try {
    if ($ForceRecreate) {
        & $PythonExe -m src.common.bootstrap_db --force-recreate
    }
    else {
        & $PythonExe -m src.common.bootstrap_db
    }
}
finally {
    Pop-Location
}

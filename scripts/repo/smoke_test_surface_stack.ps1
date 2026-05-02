[CmdletBinding()]
param(
    [string]$ApiBaseUrl = "http://127.0.0.1:8000",
    [string]$WebBaseUrl = "http://127.0.0.1:8501",
    [int]$StartupWaitSeconds = 20,
    [int]$RetryIntervalSeconds = 2
)

$ErrorActionPreference = "Stop"

function Test-EndpointWithRetries {
    param(
        [string]$Url,
        [int]$StartupWaitSeconds,
        [int]$RetryIntervalSeconds
    )

    $deadline = (Get-Date).AddSeconds($StartupWaitSeconds)
    do {
        try {
            $response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 5
            return [PSCustomObject]@{
                Url = $Url
                Ok = $true
                StatusCode = [int]$response.StatusCode
            }
        } catch {
            $statusCode = $null
            if ($_.Exception.Response -and $_.Exception.Response.StatusCode) {
                $statusCode = [int]$_.Exception.Response.StatusCode
            }
            Start-Sleep -Seconds $RetryIntervalSeconds
            $last = [PSCustomObject]@{
                Url = $Url
                Ok = $false
                StatusCode = $statusCode
            }
        }
    } while ((Get-Date) -lt $deadline)

    return $last
}

$targets = @(
    "$($ApiBaseUrl.TrimEnd('/'))/health",
    "$($ApiBaseUrl.TrimEnd('/'))/summary/latest",
    "$($ApiBaseUrl.TrimEnd('/'))/evaluation/latest",
    "$($ApiBaseUrl.TrimEnd('/'))/executive/mexico-map",
    "$($WebBaseUrl.TrimEnd('/'))/"
)

$results = @()
foreach ($target in $targets) {
    $result = Test-EndpointWithRetries -Url $target -StartupWaitSeconds $StartupWaitSeconds -RetryIntervalSeconds $RetryIntervalSeconds
    $results += $result
    Write-Host ("[smoke_test_surface_stack] {0} ok={1} status={2}" -f $result.Url, $result.Ok, $result.StatusCode)
}

$failures = @($results | Where-Object { -not $_.Ok }).Count
if ($failures -gt 0) { exit 1 }

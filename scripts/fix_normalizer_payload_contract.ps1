$path = "src\processing\normalizers.py"

$content = Get-Content $path -Raw

$old = "payload = raw_record.raw_payload"

$new = @"
# compatibility layer: support object or dict envelope
if hasattr(raw_record, "raw_payload"):
    payload = raw_record.raw_payload
elif isinstance(raw_record, dict) and "raw_payload" in raw_record:
    payload = raw_record["raw_payload"]
else:
    raise RuntimeError(f"Unsupported raw_record type: {type(raw_record)}")
"@

$content = $content.Replace($old, $new)

[System.IO.File]::WriteAllText($path, $content, (New-Object System.Text.UTF8Encoding($false)))

Write-Host "normalizers.py patched successfully"
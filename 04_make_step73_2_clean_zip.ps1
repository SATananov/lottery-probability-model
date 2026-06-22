$ErrorActionPreference = "Stop"
$env:PYTHONIOENCODING = "utf-8"

Write-Host "=== Step 73.2 clean ZIP checkpoint ==="

if (!(Test-Path ".\streamlit_app.py")) {
    throw "STOP: Run this from the project root. streamlit_app.py not found."
}

Write-Host "`n=== Git clean check ==="
$Status = git status --short
if ($Status) {
    Write-Host "STOP: Git working tree is not clean:"
    $Status
    throw "Commit/push everything first, then create clean ZIP."
}

$Commit = git rev-parse --short HEAD
$Stamp = Get-Date -Format "yyyyMMdd_HHmm"
$ProjectName = "lottery-probability-model"
$Desktop = [Environment]::GetFolderPath("Desktop")
$ZipName = "${ProjectName}_step73_2_bg-ui-polish_FINAL-clean_${Stamp}_${Commit}.zip"
$ZipPath = Join-Path $Desktop $ZipName

if (Test-Path $ZipPath) {
    Remove-Item $ZipPath -Force
}

git archive --format=zip --output="$ZipPath" HEAD

if (!(Test-Path $ZipPath)) {
    throw "STOP: ZIP was not created."
}

Write-Host "OK: ZIP created"
Write-Host "ZIP: $ZipPath"
Get-Item $ZipPath | Select-Object FullName, Length, LastWriteTime

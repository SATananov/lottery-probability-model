$ErrorActionPreference = "Stop"
$ProjectRoot = (Get-Location).Path

if (!(Test-Path (Join-Path $ProjectRoot "app.py")) -or !(Test-Path (Join-Path $ProjectRoot "data\historical_draws.csv"))) {
    throw "Run this script from the project root folder: lottery-probability-model"
}

New-Item -ItemType Directory -Force ".\r" | Out-Null
New-Item -ItemType Directory -Force ".\reports\r\plots" | Out-Null

Write-Host "R layer directories are ready."
Write-Host "If you extracted the patch ZIP, the R files are already in place."
Write-Host ""
Write-Host "Run:"
Write-Host "Rscript r/install_packages.R"
Write-Host "Rscript r/run_all_r_reports.R"

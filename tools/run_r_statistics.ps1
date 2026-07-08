$ErrorActionPreference = "Stop"

$ProjectRoot = (Get-Location).Path
$Candidates = @(
  "C:\Program Files\R\R-4.6.0\bin\Rscript.exe",
  "C:\Program Files\R\R-4.6.0\bin\x64\Rscript.exe"
)

$Rscript = $null
foreach ($Candidate in $Candidates) {
  if (Test-Path $Candidate) {
    $Rscript = $Candidate
    break
  }
}

if ($null -eq $Rscript) {
  $Found = Get-ChildItem "C:\Program Files\R" -Recurse -Filter Rscript.exe -ErrorAction SilentlyContinue | Select-Object -First 1
  if ($Found) { $Rscript = $Found.FullName }
}

if ($null -eq $Rscript) {
  throw "Rscript.exe was not found. Install R or add Rscript to PATH."
}

Write-Host "Using Rscript: $Rscript"
& $Rscript "r/install_packages.R"
& $Rscript "r/run_all_r_reports.R"

param(
    [string]$ProjectRoot = "$env:USERPROFILE\Desktop\lottery-probability-model",
    [switch]$SkipPush
)
$ErrorActionPreference = "Stop"
$ProjectRoot = (Resolve-Path $ProjectRoot).Path
if (-not (Test-Path -LiteralPath (Join-Path $ProjectRoot ".git"))) { throw "Git repository not found: $ProjectRoot" }
Push-Location $ProjectRoot
try {
    if ((git branch --show-current).Trim() -ne "main") { throw "Expected branch main." }
    git config core.autocrlf false
    python .\tools\finalize_step_151_2_2_release.py
    if ($LASTEXITCODE -ne 0) { throw "Step 151.2.2 release finalization failed." }
    git add -A
    python .\scripts\verify_step_148.py
    if ($LASTEXITCODE -ne 0) { throw "Step 148 verification failed." }
    python .\scripts\verify_step_151_2_2.py
    if ($LASTEXITCODE -ne 0) { throw "Step 151.2.2 verification failed." }
    $staged = git diff --cached --name-only
    if ($staged) { git commit -m "Repair Step 151.2.2 runtime import compatibility" }
    if (-not $SkipPush) {
        git push origin main
        if ($LASTEXITCODE -ne 0) { throw "Git push failed." }
        python .\scripts\verify_step_151_2_2.py --require-synced
        if ($LASTEXITCODE -ne 0) { throw "Post-push synchronization verification failed." }
    }
    Write-Host "STEP 151.2.2 COMPLETED SUCCESSFULLY" -ForegroundColor Green
    git status -sb
} finally { Pop-Location }

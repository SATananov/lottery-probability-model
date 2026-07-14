param(
    [string]$ProjectRoot = "$env:USERPROFILE\Desktop\lottery-probability-model",
    [switch]$SkipPush
)

$ErrorActionPreference = "Stop"
$ProjectRoot = (Resolve-Path $ProjectRoot).Path

if (-not (Test-Path -LiteralPath (Join-Path $ProjectRoot ".git"))) {
    throw "Git repository not found: $ProjectRoot"
}

Push-Location $ProjectRoot
try {
    $branch = (git branch --show-current).Trim()
    if ($branch -ne "main") {
        throw "Expected branch main, found: $branch"
    }

    git config core.autocrlf false

    $volatile = @(
        "models/v109/v109_sqlite_played_tickets_journal_model.json",
        "models/v123_bst_official_draw_detection_status.json",
        "reports/v109_sqlite_played_tickets_journal_checklist.csv",
        "reports/v109_sqlite_played_tickets_journal_summary.json",
        "reports/v109_sqlite_played_tickets_journal_summary.md",
        "reports/v123_bst_official_draw_detection_report.json",
        "reports/v123_bst_official_draw_detection_summary.md"
    )
    git restore --staged --worktree -- $volatile 2>$null

    Get-ChildItem -LiteralPath $ProjectRoot -File -Filter "CLEAN_ZIP_MANIFEST_STEP*.md" | Where-Object {
        $_.Name -ne "CLEAN_ZIP_MANIFEST_STEP151_2_1.md"
    } | Remove-Item -Force
    Get-ChildItem -LiteralPath $ProjectRoot -File -Filter "FULL_CLEAN_CHECKPOINT_MANIFEST_STEP*.md" | Where-Object {
        $_.Name -ne "FULL_CLEAN_CHECKPOINT_MANIFEST_STEP151_2_1.md"
    } | Remove-Item -Force

    # Canonicalize tracked text physically to LF before generating hash manifests.
    $eolRows = git ls-files --eol
    foreach ($row in $eolRows) {
        if ($row -notmatch "`t") { continue }
        $parts = $row -split "`t", 2
        $meta = $parts[0]
        $relative = $parts[1]
        if ($meta -notmatch "attr/text") { continue }
        if ($meta -notmatch "w/(crlf|mixed)") { continue }
        $path = Join-Path $ProjectRoot $relative
        if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { continue }
        $bytes = [System.IO.File]::ReadAllBytes($path)
        $binaryEncoding = [System.Text.Encoding]::GetEncoding(28591)
        $text = $binaryEncoding.GetString($bytes)
        $normalized = $text.Replace("`r`n", "`n")
        if ($normalized -ne $text) {
            [System.IO.File]::WriteAllBytes($path, $binaryEncoding.GetBytes($normalized))
        }
    }

    git add -A
    git add --renormalize .
    git add -A

    python .\tools\finalize_step_151_2_1_release.py
    if ($LASTEXITCODE -ne 0) { throw "Step 151.2.1 release finalization failed." }

    git add -A
    python .\scripts\verify_step_148.py
    if ($LASTEXITCODE -ne 0) { throw "Step 148 verification failed." }
    python .\scripts\verify_step_151_2_1.py
    if ($LASTEXITCODE -ne 0) { throw "Step 151.2.1 verification failed." }

    $staged = git diff --cached --name-only
    if ($staged) {
        git commit -m "Complete Step 151.2.1 user-facing backup UI separation"
        if ($LASTEXITCODE -ne 0) { throw "Git commit failed." }
    }
    else {
        Write-Host "Step 151.2.1 content is already committed." -ForegroundColor Yellow
    }

    if (-not $SkipPush) {
        git push origin main
        if ($LASTEXITCODE -ne 0) { throw "Git push failed." }
        python .\scripts\verify_step_151_2_1.py --require-synced
        if ($LASTEXITCODE -ne 0) { throw "Post-push synchronization verification failed." }
    }

    Write-Host "STEP 151.2.1 COMPLETED SUCCESSFULLY" -ForegroundColor Green
    git status -sb
}
finally {
    Pop-Location
}

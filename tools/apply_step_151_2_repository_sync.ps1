param(
    [string]$ProjectRoot = "$env:USERPROFILE\Desktop\lottery-probability-model",
    [switch]$SkipPush
)

$ErrorActionPreference = "Stop"
$ProjectRoot = (Resolve-Path $ProjectRoot).Path

if (-not (Test-Path (Join-Path $ProjectRoot ".git"))) {
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

    # Canonicalize every tracked text file physically to LF before manifest verification.
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
        # ISO-8859-1 provides a byte-for-byte round trip, so legacy source encodings are preserved.
        $binaryEncoding = [System.Text.Encoding]::GetEncoding(28591)
        $text = $binaryEncoding.GetString($bytes)
        $normalized = $text.Replace("`r`n", "`n")
        if ($normalized -ne $text) {
            [System.IO.File]::WriteAllBytes($path, $binaryEncoding.GetBytes($normalized))
        }
    }

    # Register deletions first so --renormalize never tries to stat removed legacy manifests.
    git add -A
    git add --renormalize .
    git add -A

    python .\scripts\verify_step_148.py
    python .\scripts\verify_step_151_2.py

    $staged = git diff --cached --name-only
    if (-not $staged) {
        throw "No staged Step 151.2 changes found."
    }

    git commit -m "Complete Step 151.2 repository sync and UI runtime closure"

    if (-not $SkipPush) {
        git push origin main
        python .\scripts\verify_step_151_2.py --require-synced
    }

    git status -sb
}
finally {
    Pop-Location
}

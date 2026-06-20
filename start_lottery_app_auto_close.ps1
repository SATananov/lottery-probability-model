$ErrorActionPreference = "Stop"

$Project = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Project

$Port = 8501
$Url = "http://localhost:$Port"

function Stop-Port {
    param([int]$Port)

    try {
        $connections = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
        foreach ($conn in $connections) {
            Stop-Process -Id $conn.OwningProcess -Force -ErrorAction SilentlyContinue
        }
    } catch {
    }
}

function Get-BrowserExe {
    $candidates = @(
        "$env:ProgramFiles\Microsoft\Edge\Application\msedge.exe",
        "${env:ProgramFiles(x86)}\Microsoft\Edge\Application\msedge.exe",
        "$env:ProgramFiles\Google\Chrome\Application\chrome.exe",
        "${env:ProgramFiles(x86)}\Google\Chrome\Application\chrome.exe"
    )

    foreach ($candidate in $candidates) {
        if (Test-Path $candidate) {
            return $candidate
        }
    }

    return $null
}

function Get-AppBrowserProcesses {
    param([string]$ProfileDir)

    try {
        return Get-CimInstance Win32_Process | Where-Object {
            $_.CommandLine -and $_.CommandLine.Contains($ProfileDir)
        }
    } catch {
        return @()
    }
}

Stop-Port -Port $Port

$Python = Join-Path $Project ".venv\Scripts\python.exe"
if (!(Test-Path $Python)) {
    $Python = "python"
}

Write-Host "Starting Lottery Probability Model..."
Write-Host "Please wait..."

$server = Start-Process `
    -FilePath $Python `
    -ArgumentList @("-m", "streamlit", "run", "streamlit_app.py", "--server.headless=true", "--server.port=$Port") `
    -WorkingDirectory $Project `
    -PassThru `
    -WindowStyle Hidden

$ready = $false

for ($i = 0; $i -lt 50; $i++) {
    try {
        Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 1 | Out-Null
        $ready = $true
        break
    } catch {
        Start-Sleep -Milliseconds 500
    }
}

$browserExe = Get-BrowserExe
$profileDir = Join-Path $env:TEMP "lottery_probability_model_browser_profile"

try {
    if ($browserExe) {
        New-Item -ItemType Directory -Path $profileDir -Force | Out-Null

        Start-Process `
            -FilePath $browserExe `
            -ArgumentList @("--app=$Url", "--user-data-dir=$profileDir", "--no-first-run", "--disable-background-mode") `
            -PassThru | Out-Null

        Write-Host ""
        Write-Host "App window opened."
        Write-Host "Close the app window with X to stop the app."

        Start-Sleep -Seconds 2

        while ($true) {
            $browserProcesses = @(Get-AppBrowserProcesses -ProfileDir $profileDir)
            if ($browserProcesses.Count -eq 0) {
                break
            }
            Start-Sleep -Seconds 1
        }
    } else {
        Start-Process $Url
        Write-Host ""
        Write-Host "Browser opened."
        Write-Host "Close the browser, then press ENTER here to stop the app."
        Read-Host | Out-Null
    }
}
finally {
    if ($server -and !$server.HasExited) {
        Stop-Process -Id $server.Id -Force -ErrorAction SilentlyContinue
    }

    Stop-Port -Port $Port

    Write-Host "Lottery Probability Model stopped."
    Start-Sleep -Seconds 1
}

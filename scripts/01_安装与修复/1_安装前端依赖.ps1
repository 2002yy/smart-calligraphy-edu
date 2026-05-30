[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$root = Resolve-Path (Join-Path $PSScriptRoot "..\..")
$projects = @("teacher-web", "student-app")

Write-Host "== Step 1: Install frontend dependencies ==" -ForegroundColor Cyan
Write-Host ""
Write-Host "This script will install:" -ForegroundColor Yellow
Write-Host "1. teacher-web dependencies"
Write-Host "2. student-app dependencies"
Write-Host ""

for ($i = 0; $i -lt $projects.Count; $i++) {
    $project = $projects[$i]
    Write-Host ("[{0}/{1}] Installing {2} dependencies..." -f ($i + 1), $projects.Count, $project) -ForegroundColor Yellow
    Push-Location (Join-Path $root $project)
    try {
        npm install
    }
    finally {
        Pop-Location
    }
    Write-Host ""
}

Write-Host "Done." -ForegroundColor Green

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$projectDir = Resolve-Path (Join-Path $PSScriptRoot "..\..\teacher-web")

Write-Host "== Step 2: Repair teacher-web dependencies ==" -ForegroundColor Cyan
Write-Host ""
Write-Host "Use this script when:" -ForegroundColor Yellow
Write-Host "1. npm install was interrupted"
Write-Host "2. vite cannot be found"
Write-Host "3. node_modules is broken"
Write-Host ""
Write-Host "Actions:" -ForegroundColor Yellow
Write-Host "- remove node_modules"
Write-Host "- remove package-lock.json"
Write-Host "- verify npm cache"
Write-Host "- reinstall dependencies"
Write-Host ""

Push-Location $projectDir
try {
    if (Test-Path ".\node_modules") {
        Write-Host "[1/4] Removing node_modules..." -ForegroundColor Yellow
        Remove-Item -LiteralPath ".\node_modules" -Recurse -Force
    }

    if (Test-Path ".\package-lock.json") {
        Write-Host "[2/4] Removing package-lock.json..." -ForegroundColor Yellow
        Remove-Item -LiteralPath ".\package-lock.json" -Force
    }

    Write-Host "[3/4] Verifying npm cache..." -ForegroundColor Yellow
    npm cache verify

    Write-Host "[4/4] Reinstalling teacher-web dependencies..." -ForegroundColor Yellow
    npm install --fetch-retries 5 --fetch-retry-maxtimeout 120000
}
finally {
    Pop-Location
}

Write-Host ""
Write-Host "Done." -ForegroundColor Green

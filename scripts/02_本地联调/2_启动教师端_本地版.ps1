[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Push-Location (Resolve-Path (Join-Path $PSScriptRoot "..\..\teacher-web"))
try {
    Write-Host "== Local mode: Step 2 of 3 ==" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Start teacher-web in Vite dev mode." -ForegroundColor Yellow
    Write-Host "Use this mode for:"
    Write-Host "- local UI work"
    Write-Host "- teacher-web debugging"
    Write-Host ""
    Write-Host "Next:" -ForegroundColor Yellow
    Write-Host "Open the student local script in scripts\02_本地联调"
    Write-Host ""
    npm run dev
}
finally {
    Pop-Location
}

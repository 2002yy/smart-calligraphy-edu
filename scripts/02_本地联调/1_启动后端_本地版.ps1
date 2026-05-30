[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Push-Location (Resolve-Path (Join-Path $PSScriptRoot "..\..\api-server"))
try {
    Write-Host "== Local mode: Step 1 of 3 ==" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Start api-server for local development." -ForegroundColor Yellow
    Write-Host "Use this mode for:"
    Write-Host "- local coding"
    Write-Host "- same-LAN testing"
    Write-Host "- Swagger debugging"
    Write-Host ""
    Write-Host "Next:" -ForegroundColor Yellow
    Write-Host "Open the teacher local script in scripts\02_本地联调"
    Write-Host ""
    python -m uvicorn app.main:app --reload
}
finally {
    Pop-Location
}

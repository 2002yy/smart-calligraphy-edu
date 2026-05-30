[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Push-Location (Resolve-Path (Join-Path $PSScriptRoot "..\..\student-app"))
try {
    Write-Host "== Local mode: Step 3 of 3 ==" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Start student-app in Vite dev mode." -ForegroundColor Yellow
    Write-Host "You are now in local development mode."
    Write-Host "If you need public demo mode, use scripts\03_外网演示"
    Write-Host ""
    npm run dev
}
finally {
    Pop-Location
}

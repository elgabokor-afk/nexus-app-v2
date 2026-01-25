
# NEXUS APP V2 - ONE-CLICK DEPLOY SCRIPT (V1000)
# This script automates Git staging, committing, and pushing to trigger Vercel/Railway deploys.

$ProjectDir = "C:\Users\NPC2\OneDrive\Escritorio\nexus-app-v2"
Set-Location $ProjectDir

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "   NEXUS AI - DEPLOYMENT SEQUENCE" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan

# 1. Check for changes
$status = git status --porcelain
if ($null -eq $status -or $status -eq "") {
    Write-Host "[!] No pending changes detected. System is already up to date." -ForegroundColor Yellow
    Read-Host "Press Enter to exit..."
    exit
}

Write-Host "[1/3] Staging changes..." -ForegroundColor Gray
git add .

# 2. Commit with automated message
$Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm"
$CommitMsg = "prod: nexus system update ($Timestamp)"
Write-Host "[2/3] Committing: '$CommitMsg'" -ForegroundColor Gray
git commit -m $CommitMsg

# 3. Push to Main (Triggers Pipeline)
Write-Host "[3/3] Pushing to GitHub (Vercel & Railway)..." -ForegroundColor Cyan
git push origin main

if ($LASTEXITCODE -eq 0) {
    Write-Host "=========================================" -ForegroundColor Green
    Write-Host "   SUCCESS: DEPLOYMENT TRIGGERED!" -ForegroundColor Green
    Write-Host "=========================================" -ForegroundColor Green
    Write-Host "Monitor Vercel: https://vercel.com/dashboard" -ForegroundColor Gray
    Write-Host "Monitor Railway: https://railway.app/dashboard" -ForegroundColor Gray
}
else {
    Write-Host "=========================================" -ForegroundColor Red
    Write-Host "   ERROR: Deployment failed at push stage." -ForegroundColor Red
    Write-Host "=========================================" -ForegroundColor Red
}

Read-Host "Press Enter to close..."

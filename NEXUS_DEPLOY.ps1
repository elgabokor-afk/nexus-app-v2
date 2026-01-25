
# NEXUS_DEPLOY.ps1 - Universal Deployment Script

Write-Host "🚀 Starting Nexus V2 Deployment..." -ForegroundColor Green
Write-Host "Current Directory: $(Get-Location)"

# 1. Sync Data Engine & Frontend
Write-Host "📦 Syncing Codebase..." -ForegroundColor Cyan
git add .
git commit -m "Deployment Sync"
git push

# 2. Deploy to Railway (if CLI is available)
if (Get-Command railway -ErrorAction SilentlyContinue) {
    Write-Host "🚂 Deploying to Railway..." -ForegroundColor Cyan
    railway up
}
else {
    Write-Host "⚠️ Railway CLI not found. Skipping direct deploy." -ForegroundColor Yellow
}

Write-Host "✅ Deployment Sequence Complete!" -ForegroundColor Green

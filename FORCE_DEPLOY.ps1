
# FORCE_DEPLOY.ps1 - Debug Deployment Script

$LogFile = "DEPLOY_LOG.txt"
Start-Transcript -Path $LogFile -Force

Write-Host "--- DEPLOYMENT DIAGNOSTIC STARTED ---" -ForegroundColor Cyan

# 1. Check Remote
Write-Host "1. Checking Remotes..."
git remote -v

# 2. Add All Changes
Write-Host "2. Staging Files (git add .)..."
git add .
git status

# 3. Commit
Write-Host "3. Committing..."
git commit -m "FORCE DEPLOY: Premium UI Update (V1200)"

# 4. Push
Write-Host "4. Pushing to GitHub (Origin/Main)..."
git push origin main

# 5. Check Result
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ PUSH SUCCESSFUL!" -ForegroundColor Green
}
else {
    Write-Host "❌ PUSH FAILED! Error Code: $LASTEXITCODE" -ForegroundColor Red
}

Stop-Transcript
Write-Host "Log saved to DEPLOY_LOG.txt"
Pause

@echo off
echo "========================================="
echo "   NEXUS APP V2 - AUTO DEPLOYMENT"
echo "========================================="
echo.
cd /d "c:\Users\NPC2\OneDrive\Escritorio\nexus-app-v2"
echo "1. Adding files..."
git add .
echo.
echo "2. Committing changes..."
git commit -m "feat: implement api proxy and saas ui"
echo.
echo "3. Pushing to GitHub (Vercel Deploy)..."
git push origin main
echo.
echo "========================================="
echo "   DONE! Check Vercel Dashboard."
echo "========================================="
pause

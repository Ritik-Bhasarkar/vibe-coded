@echo off
cd /d "C:\Users\ritik\ai-workspace\volunteer-dashboard"
echo Starting VolunteerFinder...
start "" /B npm run dev
timeout /t 5 /nobreak >nul
start "" "http://localhost:3000"

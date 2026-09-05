@echo off
REM Starts Docker Course Bot, dedicated Chrome, and opens the web dashboard.

echo Starting Course Bot...

echo.
echo Starting dedicated Chrome...

start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" ^
--remote-debugging-port=9222 ^
--remote-debugging-address=0.0.0.0 ^
--user-data-dir="%USERPROFILE%\chrome-bot-profile"

echo.
echo Starting Docker application...

docker compose up -d

echo.
echo Opening Course Bot...

timeout /t 3 /nobreak >nul

start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" "http://127.0.0.1:8000"
echo.
echo Course Bot started.
echo Keep this window open.

pause
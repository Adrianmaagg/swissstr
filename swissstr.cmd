@echo off
REM ======================================================================
REM  SwissSTR lokal starten  --  ein Doppelklick, alles auf diesem Laptop.
REM
REM  Kein GitHub Pages noetig: das Repo darf privat bleiben. Dieser Starter
REM  serviert SwissSTR lokal und startet den Akquise-Agenten (Heimstatt)
REM  im Hintergrund, damit der Tab "Akquise" funktioniert.
REM
REM  Stoppen: einfach die zwei kleinen Fenster (SwissSTR / Akquise-Agent)
REM  schliessen oder den Laptop neu starten.
REM ======================================================================
setlocal
set "HERE=%~dp0"
set "HEIM=C:\Users\adria\Claude\heimstatt\agent"

REM 1) Akquise-Agent im Hintergrund (ohne eigenen Browser-Tab)
if exist "%HEIM%\cockpit.cmd" (
  start "Akquise-Agent" /min "%HEIM%\cockpit.cmd" noopen
) else (
  echo HINWEIS: Heimstatt-Agent nicht gefunden unter "%HEIM%".
  echo Der Tab "Akquise" zeigt dann nur den Start-Hinweis -- der Rest laeuft normal.
)

REM 2) SwissSTR statisch servieren
start "SwissSTR-Server" /min py -3 -m http.server 8766 --directory "%HERE%."

REM 3) Browser oeffnen
timeout /t 2 >nul
start "" http://127.0.0.1:8766/index.html
echo SwissSTR laeuft lokal: http://127.0.0.1:8766/index.html
endlocal

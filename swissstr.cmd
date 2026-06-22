@echo off
REM ======================================================================
REM  SwissSTR lokal starten  --  ein Doppelklick, alles auf diesem Laptop.
REM
REM  Kein GitHub Pages noetig: das Repo darf privat bleiben. Dieser Starter
REM  serviert SwissSTR lokal und startet den Akquise-Agenten (Heimstatt)
REM  im Hintergrund, damit der Tab "Akquise" funktioniert.
REM
REM  NEU: holt beim Start automatisch den frischen Cloud-Scrape-Stand
REM  (git fast-forward) und destilliert das Briefing neu -- so hinkt der
REM  lokale Stand nie mehr hinter der taeglichen Cloud-Discovery her.
REM
REM  Stoppen: einfach die zwei kleinen Fenster (SwissSTR / Akquise-Agent)
REM  schliessen oder den Laptop neu starten.
REM ======================================================================
setlocal
set "HERE=%~dp0"
set "HEIM=C:\Users\adria\Claude\heimstatt\agent"

REM 1) Akquise-Agent im Hintergrund (zuerst, damit das Briefing gleich die
REM    Postfach-Inserate ueber /api/find-mails ziehen kann).
if exist "%HEIM%\cockpit.cmd" (
  start "Akquise-Agent" /min "%HEIM%\cockpit.cmd" noopen
) else (
  echo HINWEIS: Heimstatt-Agent nicht gefunden unter "%HEIM%".
  echo Der Tab "Akquise" zeigt dann nur den Start-Hinweis -- der Rest laeuft normal.
)

REM 2) Auto-Sync: frischen Cloud-Stand holen. Cloud = Quelle der Wahrheit fuer
REM    data/ (taeglicher Scrape). Alles best-effort + still: schlaegt git fehl
REM    (offline / divergiert / nicht installiert), startet das Tool trotzdem.
echo Hole frischen Cloud-Stand (Auto-Sync) ...
where git >nul 2>nul && (
  git -C "%HERE%." fetch --quiet origin main 2>nul
  REM lokale Scrape-Artefakte verwerfen, damit der Fast-Forward nicht blockiert
  REM (data/ wird taeglich von der Cloud erzeugt; briefing-postfach.local.json ist
  REM  gitignored und bleibt dadurch unangetastet).
  git -C "%HERE%." checkout --quiet -- data 2>nul
  git -C "%HERE%." merge --ff-only --quiet origin/main 2>nul && (
    echo   Stand aktualisiert auf neuesten Cloud-Scrape.
  ) || (
    echo   Kein Fast-Forward - lokaler Stand bleibt ^(offline oder lokale Commits^).
  )
) || echo   git nicht gefunden - ueberspringe Auto-Sync.

REM 3) Briefing lokal neu destillieren (frische Markt-Daten + Postfach-Inserate
REM    aus dem Gmail-Suchagent ueber den eben gestarteten Agenten).
py -3 "%HERE%tools\briefing.py" 2>nul

REM 4) SwissSTR statisch servieren
start "SwissSTR-Server" /min py -3 -m http.server 8766 --directory "%HERE%."

REM 5) Browser oeffnen
timeout /t 2 >nul
start "" http://127.0.0.1:8766/index.html
echo SwissSTR laeuft lokal: http://127.0.0.1:8766/index.html
endlocal

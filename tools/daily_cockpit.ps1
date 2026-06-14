# SwissSTR - TAEGLICHER Cockpit-Lauf (Free-Pipeline + Snapshot-Retention + Auto-Commit/Push).
#
# Was er macht (state of the art 2026):
#   1. Pro Fokus-Gemeinde (tools/cockpit_communes.txt) den oeffentlichen Airbnb-Kalender frisch
#      holen -> compdata.py schreibt cockpit-<m>.json (Serving) + datierten Snapshot (Historie).
#   2. Selbstheilung: scheitert eine Gemeinde, laufen die anderen weiter; ein Leer-Scrape
#      ueberschreibt den letzten guten Stand NICHT (Guard in compdata.py).
#   3. Coverage-Report (Luecken sichtbar).
#   4. Git: Snapshots + Serving-JSONs committen + pushen -> Daten liegen off-machine in GitHub.
#
# Taeglich  = nur Kalender (leicht, zuverlaessig, baut die Zeitreihe).
# -Full     = zusaetzlich Suche neu scrapen + PDP anreichern (woechentlich sinnvoll, schwerer).
# -NoPush   = lokal committen, nicht pushen (Testlauf).
#
# Manuell:  powershell -ExecutionPolicy Bypass -File tools\daily_cockpit.ps1
# Geplant:  Windows-Aufgabe "SwissSTR-Cockpit-Daily" (taeglich 06:00) - siehe tools\register_daily_task.ps1
# ASCII-only, damit Windows PowerShell 5.1 das Skript korrekt parst. Token wird NICHT gebraucht (Free-Weg).

param([switch]$Full, [switch]$NoPush)

$repo = Split-Path $PSScriptRoot -Parent
Set-Location $repo
$env:PYTHONIOENCODING = 'utf-8'
$stamp = Get-Date -Format 'yyyy-MM-dd'
$start = Get-Date
$logDir = Join-Path $repo 'data\raw'
if (-not (Test-Path $logDir)) { New-Item -ItemType Directory -Path $logDir -Force | Out-Null }
# Lock: keine parallelen Laeufe (zwei gleichzeitige Scrapes koennen competitors.json gegenseitig degradieren).
$lock = Join-Path $logDir 'daily_cockpit.lock'
if (Test-Path $lock) {
    $age = (Get-Date) - (Get-Item $lock).LastWriteTime
    if ($age.TotalMinutes -lt 90) { Write-Host ("Anderer Lauf aktiv (Lock {0} min alt) - Abbruch." -f [int]$age.TotalMinutes); exit 0 }
    Write-Host "Veralteter Lock (>90 min) - ignoriere."
}
New-Item -ItemType File -Path $lock -Force | Out-Null
try { Start-Transcript -Path (Join-Path $logDir "daily_cockpit_$stamp.log") -Append | Out-Null } catch {}

Write-Host "=================================================="
Write-Host "SwissSTR Cockpit-Daily  $stamp  (Full=$Full)"
Write-Host "=================================================="

$communesFile = Join-Path $repo 'tools\cockpit_communes.txt'
$communes = Get-Content $communesFile | Where-Object { $_ -and -not $_.TrimStart().StartsWith('#') } | ForEach-Object { $_.Trim() }

$ok = @(); $failed = @()
foreach ($m in $communes) {
    Write-Host ""
    Write-Host "----- $m -----"
    try {
        if ($Full) {
            # WICHTIG: Markt gross geschrieben (market_center/precise_query sind case-sensitiv: 'Ebikon' ja, 'ebikon' nein).
            py -3.12 tools\fetch_airbnb_free.py "$m" --market $m
            if ($LASTEXITCODE -ne 0) { throw "fetch_airbnb_free exit $LASTEXITCODE" }
            py -3.12 tools\pdp_enrich.py $m
            if ($LASTEXITCODE -ne 0) { throw "pdp_enrich exit $LASTEXITCODE" }
        }
        py -3.12 tools\compdata.py $m
        if ($LASTEXITCODE -ne 0) { throw "compdata exit $LASTEXITCODE" }
        $ok += $m
    } catch {
        Write-Host ("FEHLER bei {0}: {1}" -f $m, $_)
        $failed += $m
    }
}

Write-Host ""
Write-Host "----- Coverage -----"
py -3.12 tools\snapshot_status.py

Write-Host ""
Write-Host "----- Pickup (echte Buchungen seit dem letzten Snapshot) -----"
# Ab dem 2. Snapshot je Gemeinde: Diff -> data/cockpit-<m>-pickup.json (wird vom git-add 'cockpit-*.json' miterfasst).
py -3.12 tools\pickup.py --all --json

# --- Git: Daten durabel machen (off-machine, versioniert) ---
Write-Host ""
Write-Host "----- Git -----"
# Snapshots + Cockpit-/Pickup-JSONs IMMER; rohe Scrape-Dateien (aendern sich nur bei -Full) miterfassen.
git add data/snapshots data/cockpit-*.json data/airbnb-competitors.json data/airbnb-scrape-runs.json 2>$null
$changes = git status --porcelain -- data/snapshots data/cockpit-*.json data/airbnb-competitors.json data/airbnb-scrape-runs.json
if ($changes) {
    $msg = "data: Cockpit-Snapshots $stamp (ok: $($ok -join ',')$(if ($failed) { " ; fail: $($failed -join ',')" }))"
    git commit -m $msg | Out-Null
    if ($NoPush) {
        Write-Host "Committet (lokal, kein Push wegen -NoPush)."
    } else {
        try {
            git push origin main
            if ($LASTEXITCODE -ne 0) { throw "push exit $LASTEXITCODE" }
            Write-Host "Committet + gepusht -> Daten off-machine in GitHub."
        } catch {
            Write-Host ("WARNUNG: Push fehlgeschlagen ({0}). Commit liegt LOKAL - landet beim naechsten erfolgreichen Push in GitHub. Daten sind nicht verloren." -f $_)
        }
    }
} else {
    Write-Host "Keine Daten-Aenderungen."
}

$dur = [int]((Get-Date) - $start).TotalSeconds
Write-Host ""
Write-Host ("Fertig $stamp - ok={0} fail={1} - {2}s" -f $ok.Count, $failed.Count, $dur)
if ($failed) { Write-Host ("Fehlgeschlagen: {0}" -f ($failed -join ', ')) }
Remove-Item $lock -Force -ErrorAction SilentlyContinue
try { Stop-Transcript | Out-Null } catch {}

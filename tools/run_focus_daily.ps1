# SwissSTR - taegliche Airbnb-Sammlung fuer die Fokus-Maerkte (Preisdynamik).
# Liest tools/markets_focus.txt, scrapt pro Markt die hinterlegte URL-Liste,
# haengt einen dated Datenpunkt an die Zeitreihe (OneDrive) + aktualisiert Serving-JSON.
# Token kommt aus swissstr/.env (BRIGHTDATA_API_KEY) - nie im Skript.
# ASCII-only, damit PowerShell 5.1 (ANSI) das Skript korrekt parst.
#
# Manuell:  powershell -ExecutionPolicy Bypass -File tools\run_focus_daily.ps1
# Geplant:  Windows-Aufgabe "SwissSTR-Airbnb-Fokus" (taeglich 06:00)

$ErrorActionPreference = 'Stop'
$repo = Split-Path $PSScriptRoot -Parent
Set-Location $repo
$env:PYTHONIOENCODING = 'utf-8'
try { Start-Transcript -Path (Join-Path $repo 'data\raw\run_focus.log') -Append | Out-Null } catch {}

$focus = Get-Content "tools\markets_focus.txt" | Where-Object { $_ -and -not $_.TrimStart().StartsWith('#') }
foreach ($line in $focus) {
    $m = $line.Trim()
    if (-not $m) { continue }
    $urls = "data\airbnb-urls\$($m.ToLower()).txt"
    if (Test-Path $urls) {
        Write-Host "=== $m ==="
        python tools\fetch_airbnb.py --fetch --market $m --urls $urls
    } else {
        Write-Host "WARN: keine URL-Liste fuer $m ($urls) - uebersprungen."
    }
}
Write-Host "=== Aggregiere Zeitreihe -> Trends ==="
python tools\fetch_airbnb.py --aggregate
Write-Host ("Fertig: Fokus-Sammlung " + (Get-Date -Format 'yyyy-MM-dd HH:mm'))
try { Stop-Transcript | Out-Null } catch {}

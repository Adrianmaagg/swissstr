# SwissSTR — tägliche Airbnb-Sammlung für die Fokus-Märkte (Preisdynamik).
# Liest tools/markets_focus.txt, scrapt pro Markt die hinterlegte URL-Liste,
# hängt einen dated Datenpunkt an die Zeitreihe (OneDrive) + aktualisiert Serving-JSON.
# Token kommt aus swissstr/.env (BRIGHTDATA_API_KEY) — nie im Skript.
#
# Manuell:   powershell -ExecutionPolicy Bypass -File tools\run_focus_daily.ps1
# Geplant:   via Windows-Aufgabenplanung (schtasks) — siehe README im Daten-Archiv.

$ErrorActionPreference = 'Stop'
$repo = Split-Path $PSScriptRoot -Parent
Set-Location $repo
$env:PYTHONIOENCODING = 'utf-8'

$focus = Get-Content "tools\markets_focus.txt" | Where-Object { $_ -and -not $_.TrimStart().StartsWith('#') }
foreach ($line in $focus) {
    $m = $line.Trim()
    if (-not $m) { continue }
    $urls = "data\airbnb-urls\$($m.ToLower()).txt"
    if (Test-Path $urls) {
        Write-Host "=== $m ==="
        python tools\fetch_airbnb.py --fetch --market $m --urls $urls
    } else {
        Write-Host "WARN: keine URL-Liste fuer $m ($urls) — uebersprungen. Erst per Suche befuellen."
    }
}
Write-Host "Fertig: Fokus-Sammlung $(Get-Date -Format 'yyyy-MM-dd HH:mm')"

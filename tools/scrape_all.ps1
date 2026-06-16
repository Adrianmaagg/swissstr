# SwissSTR - BATCH-Scrape ueber VIELE Maerkte (Free-Pipeline).
#
# Pro Markt die Voll-Rezeptur (wie fuer die 6 Fokus-Gemeinden, jetzt automatisch):
#   1. Grenze holen (fetch_boundary.py)  -- nur wenn boundary-<m>.geojson fehlt
#   2. Center ableiten (ensure_center.py) -- Centroid der Grenze; ohne Center flaggt der
#      Scraper UNUSABLE (Zermatt-Befund)
#   3. Free-Scrape (fetch_airbnb_free.py) -- Mehr-Fenster-Discovery + Kalender
#   4. PDP anreichern (pdp_enrich.py)     -- Objektart/Superhost/Host-ID
#   5. compdata.py                        -- cockpit-<m>.json (Guard: 0 Inserate -> kein Ueberschreiben)
#
# Wiederaufnehmbar: Maerkte mit cockpit-<m>.json von HEUTE werden uebersprungen (ausser -Force).
# Hoeflich: -DelaySec Pause zwischen Maerkten (Default 8s) gegen Rate-Limit/Sperre.
# Gestaffelt: -Limit N verarbeitet nur N Maerkte pro Lauf (mehrmals laufen lassen).
#
# Aufruf:  powershell -ExecutionPolicy Bypass -File tools\scrape_all.ps1 -Limit 10
#          ... -Markets "Chur,Interlaken,Davos"
#          ... -Force   (auch heute schon Gescrapte neu)
# Liste:   tools\scrape_markets.txt  (Zeilen "Name|Geocode-Query")
# ASCII-only fuer Windows PowerShell 5.1.

param(
  [int]$Limit = 0,
  [string]$Markets = "",
  [int]$DelaySec = 8,
  [switch]$Force
)

$repo = Split-Path $PSScriptRoot -Parent
Set-Location $repo
$env:PYTHONIOENCODING = 'utf-8'
$py = 'python'
$stamp = Get-Date -Format 'yyyy-MM-dd'
$today = (Get-Date).Date
$logDir = Join-Path $repo 'data\raw'
if (-not (Test-Path $logDir)) { New-Item -ItemType Directory -Path $logDir -Force | Out-Null }

# Lock: keine parallelen Laeufe (degradiert competitors.json gegenseitig).
$lock = Join-Path $logDir 'scrape_all.lock'
if (Test-Path $lock) {
  $age = (Get-Date) - (Get-Item $lock).LastWriteTime
  if ($age.TotalMinutes -lt 720) { Write-Host ("Anderer Batch aktiv (Lock {0} min) - Abbruch." -f [int]$age.TotalMinutes); exit 0 }
}
New-Item -ItemType File -Path $lock -Force | Out-Null
try { Start-Transcript -Path (Join-Path $logDir "scrape_all_$stamp.log") -Append | Out-Null } catch {}

function Run-Py($scriptArgs, $timeoutSec) {
  # Ruft python tools\<script> auf; gibt $true/$false zurueck. Timeout via Job.
  $job = Start-Job -ScriptBlock {
    param($repo, $a)
    Set-Location $repo; $env:PYTHONIOENCODING = 'utf-8'
    & python @a 2>&1
  } -ArgumentList $repo, $scriptArgs
  if (Wait-Job $job -Timeout $timeoutSec) {
    Receive-Job $job | ForEach-Object { Write-Host "    $_" }
    $ok = ($job.State -eq 'Completed')
  } else {
    Stop-Job $job; Write-Host "    [TIMEOUT nach ${timeoutSec}s]"; $ok = $false
  }
  Remove-Job $job -Force
  return $ok
}

# Markt-Liste laden
$lines = Get-Content (Join-Path $repo 'tools\scrape_markets.txt') | Where-Object { $_ -and -not $_.StartsWith('#') }
$only = @()
if ($Markets) { $only = $Markets.Split(',') | ForEach-Object { $_.Trim() } }

$done = 0; $ok = 0; $fail = 0; $skip = 0
$total = $lines.Count
Write-Host "=================================================="
Write-Host "SwissSTR Batch-Scrape  $stamp  (Limit=$Limit Delay=${DelaySec}s Force=$Force)"
Write-Host "Maerkte in Liste: $total"
Write-Host "=================================================="

foreach ($line in $lines) {
  $parts = $line.Split('|')
  $name = $parts[0].Trim()
  $query = if ($parts.Count -gt 1) { $parts[1].Trim() } else { "$name, Switzerland" }
  if ($only.Count -gt 0 -and ($only -notcontains $name)) { continue }
  if ($Limit -gt 0 -and $done -ge $Limit) { break }

  $cock = Join-Path $repo ("data\cockpit-{0}.json" -f $name.ToLower())
  if (-not $Force -and (Test-Path $cock) -and ((Get-Item $cock).LastWriteTime.Date -eq $today)) {
    $skip++; continue
  }

  $done++
  Write-Host ("[{0}/{1}] {2}" -f $done, $(if ($Limit -gt 0) { $Limit } else { $total }), $name)
  $bound = Join-Path $repo ("data\boundary-{0}.geojson" -f $name.ToLower())
  try {
    if (-not (Test-Path $bound)) {
      Write-Host "  Grenze holen ..."
      Run-Py @('tools\fetch_boundary.py', $name, $query) 60 | Out-Null
      Start-Sleep -Seconds 1   # Nominatim hoeflich
    }
    Run-Py @('tools\ensure_center.py', $name) 30 | Out-Null
    Write-Host "  Scrape ..."
    $sok = Run-Py @('tools\fetch_airbnb_free.py', $query, '--market', $name) 360
    if ($sok) {
      Run-Py @('tools\pdp_enrich.py', $name) 240 | Out-Null
      $cok = Run-Py @('tools\compdata.py', $name) 240
      if ((Test-Path $cock) -and ((Get-Item $cock).LastWriteTime.Date -eq $today)) {
        $ok++; Write-Host "  OK -> $cock"
      } else {
        $fail++; Write-Host "  KEINE verwertbaren Daten (Guard) - letzter Stand bleibt."
      }
    } else {
      $fail++; Write-Host "  Scrape fehlgeschlagen/Timeout."
    }
  } catch {
    $fail++; Write-Host ("  FEHLER: {0}" -f $_.Exception.Message)
  }
  Start-Sleep -Seconds $DelaySec
}

Write-Host "Markt-Manifest + Host-Portfolios aktualisieren ..."
Run-Py @('tools\build_market_manifest.py') 60 | Out-Null
Run-Py @('tools\build_host_portfolios.py') 60 | Out-Null
Write-Host "=================================================="
Write-Host ("Fertig: {0} verarbeitet, {1} ok, {2} fail, {3} schon-frisch-uebersprungen." -f $done, $ok, $fail, $skip)
Write-Host "Naechster Schritt: index.html im Browser oeffnen -> exportMarketFacts() -> market-facts.json frisch -> Atlas."
Write-Host "=================================================="
try { Stop-Transcript | Out-Null } catch {}
Remove-Item $lock -Force -ErrorAction SilentlyContinue

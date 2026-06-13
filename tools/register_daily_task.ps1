# Registriert die Windows-Aufgabe "SwissSTR-Cockpit-Daily" (taeglich 06:00 -> tools\daily_cockpit.ps1).
# Idempotent (-Force ueberschreibt). Braucht KEINE Admin-Rechte (Aufgabe im eigenen Benutzer-Kontext).
#
#   powershell -ExecutionPolicy Bypass -File tools\register_daily_task.ps1
#   powershell -ExecutionPolicy Bypass -File tools\register_daily_task.ps1 -At 06:00 -Unregister   (entfernen)

param([string]$At = '06:00', [switch]$Unregister)

$taskName = 'SwissSTR-Cockpit-Daily'
$repo = Split-Path $PSScriptRoot -Parent
$script = Join-Path $repo 'tools\daily_cockpit.ps1'

if ($Unregister) {
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction SilentlyContinue
    Write-Host "Aufgabe '$taskName' entfernt (falls vorhanden)."
    return
}

if (-not (Test-Path $script)) { throw "daily_cockpit.ps1 nicht gefunden: $script" }

$action = New-ScheduledTaskAction -Execute 'powershell.exe' `
    -Argument "-NoProfile -NonInteractive -ExecutionPolicy Bypass -File `"$script`"" `
    -WorkingDirectory $repo
$trigger = New-ScheduledTaskTrigger -Daily -At $At
# State of the art: verpasste Laeufe nachholen (PC war aus), aus Schlaf wecken, Laptop-tauglich,
# bei Fehler 2x neu versuchen, max. 1h Laufzeit.
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -WakeToRun `
    -ExecutionTimeLimit (New-TimeSpan -Hours 1) `
    -RestartCount 2 -RestartInterval (New-TimeSpan -Minutes 10) `
    -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
# S4U: laeuft, ob eingeloggt oder nicht, ohne gespeichertes Passwort.
$principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -LogonType S4U -RunLevel Limited

Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Settings $settings `
    -Principal $principal -Force `
    -Description "Taeglicher SwissSTR Cockpit-Lauf: Airbnb-Kalender je Fokus-Gemeinde -> dated Snapshot -> git commit + push. Free-Pipeline, kein API-Key." | Out-Null

$t = Get-ScheduledTask -TaskName $taskName
$info = Get-ScheduledTaskInfo -TaskName $taskName
Write-Host "Aufgabe '$taskName' registriert."
Write-Host ("  Status:        {0}" -f $t.State)
Write-Host ("  Naechster Lauf: {0}" -f $info.NextRunTime)
Write-Host "  Manuell testen: Start-ScheduledTask -TaskName '$taskName'   (oder tools\daily_cockpit.ps1 -NoPush)"

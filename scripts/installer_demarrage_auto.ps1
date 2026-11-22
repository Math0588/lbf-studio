# Crée une tâche planifiée Windows qui lance le studio à l'ouverture de session (production de la réserve).
# À lancer UNE fois, par toi, dans PowerShell :  powershell -ExecutionPolicy Bypass -File scripts\installer_demarrage_auto.ps1
# Pour l'enlever :  Unregister-ScheduledTask -TaskName "LeBordelFrancais" -Confirm:$false
$root = Split-Path -Parent $PSScriptRoot
$action = New-ScheduledTaskAction -Execute "cmd.exe" -Argument "/c `"$root\Demarrer.bat`" auto" -WorkingDirectory $root
$trigger = New-ScheduledTaskTrigger -AtLogOn
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
Register-ScheduledTask -TaskName "LeBordelFrancais" -Action $action -Trigger $trigger -Settings $settings `
  -Description "Studio Le Bordel Français : fabrique la réserve de vidéos et l'envoie au diffuseur cloud." -Force
Write-Host "Tâche installée : le studio démarrera à chaque ouverture de session."

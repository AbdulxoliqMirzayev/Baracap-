@echo off
setlocal

net session >nul 2>&1
if %errorlevel% neq 0 (
  echo Requesting administrator permission...
  powershell -NoProfile -ExecutionPolicy Bypass -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
  exit /b
)

echo Opening Windows Firewall for BARACAP on port 8000...
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$ruleName='BARACAP local dev port 8000';" ^
  "$existing=Get-NetFirewallRule -DisplayName $ruleName -ErrorAction SilentlyContinue;" ^
  "if (-not $existing) { New-NetFirewallRule -DisplayName $ruleName -Direction Inbound -Action Allow -Protocol TCP -LocalPort 8000 -Profile Private,Public | Out-Null }" ^
  "else { Set-NetFirewallRule -DisplayName $ruleName -Enabled True -Action Allow -Profile Private,Public | Out-Null }"

echo Setting connected network profile to Private...
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "Get-NetConnectionProfile | Where-Object {$_.IPv4Connectivity -ne 'Disconnected'} | Set-NetConnectionProfile -NetworkCategory Private"

echo.
echo Done. Open this on your phone:
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$ip=(Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.IPAddress -notlike '127.*' -and $_.PrefixOrigin -ne 'WellKnown' } | Select-Object -First 1 -ExpandProperty IPAddress); Write-Host ('http://' + $ip + ':8000')"
echo.
pause

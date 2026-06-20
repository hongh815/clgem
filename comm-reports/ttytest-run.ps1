$ErrorActionPreference = 'Continue'
$log = "$PSScriptRoot\ttytest.log"
Remove-Item $log -ErrorAction SilentlyContinue
Start-Transcript -Path $log -Force | Out-Null
Write-Host "=== TTY transcript test ==="
agy --dangerously-skip-permissions --model "Gemini 3.1 Pro (High)" --print-timeout 90s -p "Reply with exactly this token then a one-sentence note: TTYTEST_OK"
Stop-Transcript | Out-Null
"DONE_MARKER" | Out-File -FilePath "$PSScriptRoot\ttytest.done" -Encoding utf8

$ErrorActionPreference = 'Continue'
Write-Host "=== clgem R1 review — agy (Gemini 3.1 Pro (High)), 자동 캡처 → R1.log ===" -ForegroundColor Cyan
Write-Host ""
$p = Get-Content "$PSScriptRoot\R1-prompt.txt" -Raw
# 실제 콘솔(TTY) + --dangerously-skip-permissions(사용자 승인) → print 출력됨. Tee-Object로 캡처.
agy --dangerously-skip-permissions --model "Gemini 3.1 Pro (High)" --print-timeout 6m `
    --add-dir "C:\Users\hongh\.claude\skills\clgem" `
    --add-dir "$PSScriptRoot" `
    -p $p | Tee-Object -FilePath "$PSScriptRoot\R1.log"
Write-Host ""
Write-Host "=== R1 review complete — verdict saved to R1.log ===" -ForegroundColor Green

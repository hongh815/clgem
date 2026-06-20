$ErrorActionPreference = 'Continue'
Write-Host "=== clgem R3 — agy 대화형 독립 검토 (Gemini 3.1 Pro (High)) ===" -ForegroundColor Cyan
Write-Host "퍼미션(파일 읽기 등) 요청이 뜨면 직접 승인하세요. opus 검토는 별도로 병렬 진행됩니다." -ForegroundColor DarkGray
Write-Host "검토가 끝나면 VERDICT/FINDINGS 블록을 확인하세요(필요 시 Claude에 전달)." -ForegroundColor DarkGray
Write-Host ""
$p = Get-Content "$PSScriptRoot\R3-prompt.txt" -Raw
# 대화형: 사용자가 퍼미션을 직접 처리(--dangerously-skip-permissions 사용 안 함).
agy --prompt-interactive $p `
    --model "Gemini 3.1 Pro (High)" `
    --add-dir "C:\Users\hongh\.claude\skills\clgem"
Write-Host ""
Write-Host "=== agy R3 세션 종료 ===" -ForegroundColor Green

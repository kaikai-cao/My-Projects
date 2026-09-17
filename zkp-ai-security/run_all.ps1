# run_all.ps1
$ErrorActionPreference = "Stop"

Write-Host "=== Activating venv ===" -ForegroundColor Cyan
.\.venv\Scripts\Activate.ps1

Write-Host "`n=== Stage A ===" -ForegroundColor Cyan
python stage_a\extract.py

Write-Host "`n=== Stage B ===" -ForegroundColor Cyan
python stage_b\build_prompt.py

Write-Host "`n=== Stage C ===" -ForegroundColor Cyan
python stage_c\call_llm.py

Write-Host "`n=== Stage D ===" -ForegroundColor Cyan
python stage_d\cross_check.py

Write-Host "`n=== Stage E ===" -ForegroundColor Cyan
python stage_e\evaluate.py

Write-Host "`nAll stages complete." -ForegroundColor Green
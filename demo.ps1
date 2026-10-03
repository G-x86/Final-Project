# เดโมวันพรีเซนต์: รันทีเดียวโชว์ทั้งสาย (self-check -> agent -> eval)
Write-Host "=== 1/3 self-check tools ===" -ForegroundColor Cyan
python tools.py
Write-Host ""
Write-Host "=== 2/3 agent ซ่อมบั๊กสด ===" -ForegroundColor Cyan
python agent.py "ซ่อมบั๊กแล้วเขียน patch" --yes
Write-Host ""
Write-Host "=== 3/3 eval 10 งาน ===" -ForegroundColor Cyan
python eval/eval.py

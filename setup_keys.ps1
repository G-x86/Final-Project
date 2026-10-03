# ตั้ง API key แบบไม่ต้องพิมพ์ key ลงแชท/โค้ด
# ใช้:  .\setup_keys.ps1            (มีผลเฉพาะหน้าต่างนี้)
#       .\setup_keys.ps1 -Save      (บันทึกใส่ .env ใช้รอบหน้าได้เลย)
param([switch]$Save)

$choice = Read-Host "เลือก provider [1=openrouter(free) / 2=deepseek / 3=ollama local(ไม่ต้องมี key)]"
if ($choice -eq "3") {
    $env:LLM_BASE_URL = "http://localhost:11434/v1"
    Write-Host "ใช้ ollama บนเครื่อง ไม่ต้องมี key" -ForegroundColor Green
    if ($Save) { "LLM_BASE_URL=http://localhost:11434/v1" | Set-Content ".env" -Encoding UTF8 }
    exit 0
}
if ($choice -eq "2") {
    $keyName = "DEEPSEEK_API_KEY"; $defModel = "deepseek-chat"; $prov = "deepseek"
} else {
    $keyName = "OPENROUTER_API_KEY"; $defModel = "z-ai/glm-4.5:free"; $prov = "openrouter"
}
$sec = Read-Host "วาง $keyName (จอไม่โชว์ตัวอักษร)" -AsSecureString
$key = [Runtime.InteropServices.Marshal]::PtrToStringAuto(
    [Runtime.InteropServices.Marshal]::SecureStringToBSTR($sec))
if (-not $key) { Write-Host "key ว่าง ยกเลิก" -ForegroundColor Red; exit 1 }
[Environment]::SetEnvironmentVariable($keyName, $key, "Process")
Set-Item "env:$keyName" $key
$model = Read-Host "ชื่อโมเดล (ว่าง = $defModel)"
if (-not $model) { $model = $defModel }
$env:LLM_MODEL = $model
if ($Save) {
    "$keyName=$key", "LLM_MODEL=$model" | Set-Content ".env" -Encoding UTF8
    Write-Host "บันทึก .env แล้ว (ไฟล์นี้ห้ามคอมมิต)" -ForegroundColor Yellow
}
Write-Host "พร้อมใช้: python agent.py `"ซ่อมบั๊กแล้วเขียน patch`" --yes --provider $prov" -ForegroundColor Green

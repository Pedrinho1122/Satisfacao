# Script PowerShell para manter o servidor sempre ativo
$scriptPath = "C:\Users\ESRP\Desktop\Satisfacao"
$pythonPath = "C:\Users\ESRP\Desktop\Cliques\.venv\Scripts\python.exe"
$appPath = "C:\Users\ESRP\Desktop\Satisfacao\app.py"

Set-Location $scriptPath

Write-Host "========================================" -ForegroundColor Cyan
Write-Host " Servidor Satisfacao - Auto Restart" -ForegroundColor Green
Write-Host " Pressione CTRL+C para parar" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

while ($true) {
    Write-Host "[$(Get-Date -Format 'HH:mm:ss')] Iniciando servidor..." -ForegroundColor Green
    
    $process = Start-Process -FilePath $pythonPath -ArgumentList $appPath -NoNewWindow -PassThru
    
    # Aguardar o processo terminar
    $process.WaitForExit()
    
    Write-Host "[$(Get-Date -Format 'HH:mm:ss')] Servidor parou! Reiniciando em 3 segundos..." -ForegroundColor Yellow
    Start-Sleep -Seconds 3
}

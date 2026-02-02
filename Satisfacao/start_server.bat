@echo off
cd /d C:\Users\ESRP\Desktop\Satisfacao

:loop
echo.
echo ========================================
echo  Iniciando servidor Satisfacao...
echo  Pressione CTRL+C para parar
echo ========================================
echo.

C:\Users\ESRP\Desktop\Cliques\.venv\Scripts\python.exe app.py

echo.
echo Servidor parou! Reiniciando em 2 segundos...
timeout /t 2 /nobreak > nul
goto loop

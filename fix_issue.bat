@echo off
:: Obtém o caminho da pasta onde o .bat está
set "PROJECT_ROOT=%~dp0"

:: Define os caminhos relativos para os executáveis
set "CHROME_PATH=%PROJECT_ROOT%bin\chrome-win64\chrome.exe"
set "DRIVER_PATH=%AppData%\undetected_chromedriver\undetected_chromedriver.exe"

:: Executa o comando PowerShell para desbloquear os arquivos
powershell -Command "Unblock-File -Path '%CHROME_PATH%'"
powershell -Command "Unblock-File -Path '%DRIVER_PATH%'"

if %ERRORLEVEL% EQU 0 (
    echo [SUCESSO] Arquivos desbloqueados com sucesso!
) else (
    echo [ERRO] Falha ao desbloquear arquivos. Tente rodar como Administrador.
)

pause
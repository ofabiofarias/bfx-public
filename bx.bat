@echo off
setlocal EnableDelayedExpansion
chcp 65001 > nul
pushd "%~dp0"

title [bx] borderô extractor
color 0F

for /f %%a in ('powershell -command "[char]27"') do set ESC=%%a
set "BLUE=%ESC%[38;2;0;85;164m"
set "WHITE=%ESC%[38;2;255;255;255m"
set "RED=%ESC%[38;2;239;65;53m"
set "GRAY=%ESC%[90m"
set "RESET=%ESC%[0m"

cls
echo.
echo %BLUE%       __%WHITE%       %RED%       %RESET%
echo %BLUE%      / /_%WHITE%_  __ %RED%       %RESET%
echo %BLUE%     / __ \%WHITE% \/ / %RED%      %RESET%
echo %BLUE%    / /_/ /%WHITE%^>  ^<  %RED%      %RESET%
echo %BLUE%   /_.___/%WHITE%_/\_\ %RED%      %RESET%
echo %BLUE% ▀▀▀▀▀▀▀▀%WHITE%▀▀▀▀▀▀▀%RED%▀▀▀▀▀▀▀▀%RESET%
echo    %GRAY%borderô extractor%RESET%
echo.
echo   %GRAY%[%BLUE%r.lab%GRAY%]%RESET% • fabio farias
echo.
echo %GRAY%---------------------------------%RESET%
echo  %BLUE%::%RESET% %WHITE%Verificando dependencias...%RESET%
python -m pip install -r requirements.txt -q
if %ERRORLEVEL% neq 0 (
    echo  %RED%[x] Erro ao instalar dependencias.%RESET%
    pause
    exit /b 1
)

echo  %RED%::%RESET% %WHITE%Inicializando sistema...%RESET%
echo.
python -m streamlit run app.py

if %ERRORLEVEL% neq 0 (
    echo.
    echo  %RED%[x] Instância encerrada.%RESET%
    pause
)

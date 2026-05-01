@echo off
setlocal

title PocketMedic Builder

echo.
echo ========================================
echo          PocketMedic EXE Builder
echo ========================================
echo.

set "EXE_NAME="
set /p "EXE_NAME=Enter EXE Name: "

if "%EXE_NAME%"=="" (
    echo.
    echo No EXE name entered. Build canceled.
    echo.
    pause
    exit /b 1
)

echo.
echo Building PocketMedic as "%EXE_NAME%.exe"...
echo.

python -m PyInstaller ^
    --clean ^
    --noconfirm ^
    --onefile ^
    --console ^
    --name "%EXE_NAME%" ^
    --distpath "dist" ^
    --workpath "build" ^
    --add-data "Config;Config" ^
    PocketMedic.py

if errorlevel 1 (
    echo.
    echo Build failed.
    echo.
    pause
    exit /b 1
)

echo.
echo Build completed successfully.
echo Output:
echo dist\%EXE_NAME%.exe
echo.

pause
endlocal

@echo off
setlocal EnableExtensions

title PocketMedic Rebuild

echo.
echo ========================================
echo          PocketMedic Rebuild
echo ========================================
echo.

set "EXE_NAME="
set /p "EXE_NAME=Enter EXE Name: "

if "%EXE_NAME%"=="" (
    echo.
    echo No EXE name entered. Build canceled.
    goto fail
)

echo.
echo Preparing rebuild for "%EXE_NAME%.exe"...
echo.

echo [1/7] Cleaning old build output...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"
if exist "%EXE_NAME%.spec" del /q "%EXE_NAME%.spec"

echo.
echo [2/7] Installing and updating dependencies...
python -m pip install -r requirements.txt
if errorlevel 1 goto fail

python -m pip install pyinstaller
if errorlevel 1 goto fail

echo.
echo [3/7] Running syntax check...
python -m py_compile PocketMedic.py
if errorlevel 1 goto fail

echo.
echo [4/7] Verifying required folders...
if not exist "Config" (
    echo Missing required folder: Config
    goto fail
)

echo.
echo [5/7] Creating optional external folders if needed...
if not exist "Installers" mkdir "Installers"
if not exist "PortableTools" mkdir "PortableTools"
if not exist "PocketMedic_Data" mkdir "PocketMedic_Data"
if not exist "PocketMedic_Data\Installers" mkdir "PocketMedic_Data\Installers"

if not exist "Installers" goto fail
if not exist "PortableTools" goto fail
if not exist "PocketMedic_Data" goto fail
if not exist "PocketMedic_Data\Installers" goto fail

echo.
echo [6/7] Building PocketMedic with PyInstaller...
python -m PyInstaller ^
    --clean ^
    --noconfirm ^
    --onefile ^
    --console ^
    --name "%EXE_NAME%" ^
    --distpath "dist" ^
    --workpath "build" ^
    --specpath "." ^
    --add-data "Config;Config" ^
    PocketMedic.py
if errorlevel 1 goto fail

echo.
echo [7/7] Verifying final EXE...
if not exist "dist\%EXE_NAME%.exe" goto fail

echo.
echo Build completed successfully.
echo Output path:
echo dist\%EXE_NAME%.exe
echo.
goto done

:fail
echo.
echo Build failed or was canceled.
echo.
pause
exit /b 1

:done
pause
endlocal

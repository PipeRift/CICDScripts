@echo off > nul
setlocal EnableDelayedExpansion > nul

if not defined plugin ( set plugin=%1 )
if not defined engine_version ( set engine_version=%2 )

if "!plugin!" EQU "" (
    echo "No plugin name specified"
    exit 1
)
if "!engine_version!" EQU "" (
    echo "No engine subversion(4.X) specified"
    exit 1
)
set dot_version=4.!engine_version!
set compact_version=4!engine_version!


set project_path=%CI_PROJECT_DIR%

set lib_path=%~dp0
set build_path=!project_path!\Build


IF NOT EXIST !build_path!\!plugin!_!compact_version! (
    echo "\Build\!plugin!_!compact_version!" doesn't exist
    exit 1
)

echo.
echo -- Cleanup Deployment Folder
rmdir "!build_path!\!plugin!" /S /Q 2> nul
mkdir "!build_path!\!plugin!" > nul

echo -- Remove old packaged Plugin
del "!build_path!\!plugin!_!compact_version!.zip" 2> nul
del "!build_path!\!plugin!_!compact_version!_Bin.zip" 2> nul

echo -- Cleanup Online Documentation
rmdir "!build_path!\!plugin!_!dot_version!\Docs" /S /Q > nul

echo.
echo -- Copy !dot_version! Plugin
echo     \!plugin!_!compact_version! into \!plugin!
xcopy "!build_path!\!plugin!_!compact_version!" "!build_path!\!plugin!" /S /Q /Y > nul
if errorlevel 1  ( exit 1 )

echo.
echo -- Copy Config
mkdir "!build_path!\!plugin!\Config" > nul
xcopy "!build_path!\Config" "%cd%\!plugin!\Config" /S /Q /Y > nul

echo.
echo -- Compress Plugin with Binaries
call "!lib_path!/bin/7z" a !build_path!/!plugin!!compact_version!_Bin.zip !build_path!/!plugin! > nul
if errorlevel 1  ( exit 1 )

echo.
echo -- Cleanup Plugin Binaries
rmdir "!build_path!\!plugin!\Binaries" /S /Q > nul
rmdir "!build_path!\!plugin!\Intermediate" /S /Q > nul
if errorlevel 1  ( exit 1 )

echo -- Compress Plugin
call "!lib_path!/bin/7z" a !build_path!/!plugin!!compact_version!.zip !build_path!/!plugin! > nul
if errorlevel 1  ( exit 1 )

echo.
rmdir "!build_path!\!plugin!" /S /Q > nul

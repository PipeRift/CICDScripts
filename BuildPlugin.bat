@echo off
setlocal EnableDelayedExpansion

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

cd !project_path!

echo.
echo -- Building !Plugin! Plugin
echo.

call ue4 uat BuildPlugin -Plugin="!project_path!\!plugin!.uplugin" -Package="!build_path!\!plugin!_!compact_version!" -Rocket
if errorlevel 1  ( exit 1 )

echo.
echo done

exit
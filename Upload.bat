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

set mega_folder=F:/Mega

IF NOT EXIST !mega_folder!/Piperift/!plugin!/Last (
  echo -- Create storage folder
  mkdir "!mega_folder!/Piperift/!plugin!/Last" > nul
  if errorlevel 1  ( exit 1 )
)

echo -- Storing files
mkdir "!mega_folder!/Piperift/!plugin!/Last/!CI_COMMIT_REF_NAME!" > nul

xcopy "!build_path!\!plugin!!compact_version!.zip" "!mega_folder!/Piperift/!plugin!/Last/!CI_COMMIT_REF_NAME!" /Q /Y
xcopy "!build_path!\!plugin!!compact_version!_Bin.zip" "!mega_folder!/Piperift/!plugin!/Last/!CI_COMMIT_REF_NAME!" /Q /Y
if errorlevel 1  ( exit 1 )
echo.

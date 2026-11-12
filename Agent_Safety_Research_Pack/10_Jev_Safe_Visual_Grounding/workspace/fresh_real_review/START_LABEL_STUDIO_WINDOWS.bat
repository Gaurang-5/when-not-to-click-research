@echo off
cd /d "%~dp0"
set LOCAL_FILES_SERVING_ENABLED=true
set LOCAL_FILES_DOCUMENT_ROOT=%CD%
label-studio start --port 8080
if errorlevel 1 (
  echo Label Studio was not found. Activate the Python environment where it is installed and run this file again.
  pause
)

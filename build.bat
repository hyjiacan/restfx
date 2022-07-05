@echo off

call venv\Scripts\activate

set params=

:param
set str=%1
if "%str%"=="" (
    goto exec
)
set params=%params% %str%
shift /0
goto param

:exec

if exist dist (
    rmdir /S /Q dist
)
if exist build (
    rmdir /S /Q build
)
if exist src\restfx.egg-info (
    rmdir /S /Q src\restfx.egg-info
)

python pack.py %params%

if %errorlevel% NEQ 0 (
    goto end
)

python setup.py sdist bdist_wheel

:end

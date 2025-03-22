@echo off
SETLOCAL

:: Check if Python is installed
python --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo Error: Python is not installed. Please install Python and try again.
    EXIT /B 1
)

:: Switch to current directory
SET "CURR_DIR=%CD%"

pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: pip is not installed.
    exit /b 1
)

:: Check if the 'docker' Python module is installed
python -c "import docker" 2>nul
if %errorlevel% neq 0 (
    echo Docker module not found. Installing...
    pip install docker
    if %errorlevel% neq 0 (
        echo Error: Failed to install the docker module.
        exit /b 1
    )
) else (
    echo Docker module is already installed.
)

:: Read git.ini file
SET "GIT_INI=%CURR_DIR%\git.ini"
IF NOT EXIST "%GIT_INI%" (
    echo Error: git.ini file not found.
    EXIT /B 1
)

:: Update git.ini file with client input and free ports
IF EXIST "%CURR_DIR%\gitini_ports_update.py" (
    echo Running gitini_ports_update.py...
    python "%CURR_DIR%\gitini_ports_update.py"
    IF %ERRORLEVEL% NEQ 0 (
        echo Error: gitini_ports_update.py execution failed.
        EXIT /B 1
    )
)

:: Check if update_configini_file.py exists in the same directory as this batch file
IF EXIST "%CURR_DIR%\update_configini_file.py" (
    echo Running update_configini_file.py...
    python "%CURR_DIR%\update_configini_file.py"
    IF %ERRORLEVEL% NEQ 0 (
        echo Error: update_configini_file.py execution failed.
        EXIT /B 1
    )
)

:: Run the Python script
python 01_start.py
IF %ERRORLEVEL% NEQ 0 (
    echo Error: Python script execution failed.
    EXIT /B 1
)

:: Switch to current directory
SET "CURR_DIR=%CD%"

FOR /F "tokens=1,2 delims==" %%A IN ('findstr "home_dir" "%GIT_INI%"') DO (
    IF "%%A" == "home_dir" SET "HOME_DIR=%%B"
)

:: Check if home_dir exists
IF NOT EXIST "%CURR_DIR%\%HOME_DIR%" (
    echo Error: Home directory %HOME_DIR% not found.
    EXIT /B 1
)

:: Copy config.ini from CURR_DIR to HOME_DIR
IF EXIST "%CURR_DIR%\config.ini" (
    COPY /Y "%CURR_DIR%\config.ini" "%CURR_DIR%\%HOME_DIR%\"
    IF %ERRORLEVEL% NEQ 0 (
        echo Error: Failed to copy config.ini to %HOME_DIR%.
        EXIT /B 1
    )
) ELSE (
    echo Warning: config.ini not found in %CURR_DIR%.
)

:: Switch to home directory and then to config directory
CD /D "%CURR_DIR%\%HOME_DIR%\config"
IF NOT EXIST "run_python.bat" (
    echo Error: run_python.bat not found.
    EXIT /B 1
)

:: Run run_python.bat
call run_python.bat
IF %ERRORLEVEL% NEQ 0 (
    echo Error: run_python.bat execution failed.
    EXIT /B 1
)

echo Current Directory: %CD%
:: Switch to home directory
CD /D "%CURR_DIR%\%HOME_DIR%"


echo After switching what Current Directory: %CD%

:: Check if docker-compose.yml exists
IF EXIST "docker-compose.yml" (
    IF EXIST "docarize.bat" (
        call docarize.bat
    ) ELSE (
        echo Warning: dockerize.bat not found.
    )
) ELSE (
    echo Warning: docker-compose.yml not found.
)

:: Switch back to CURR_DIR
CD /D "%CURR_DIR%"

:: Check if get_results.py exists and run it
IF EXIST "%CURR_DIR%\get_results.py" (
    echo Running get_results.py...
    python "%CURR_DIR%\get_results.py"
    IF %ERRORLEVEL% NEQ 0 (
        echo Error: get_results.py execution failed.
        EXIT /B 1
    )
) ELSE (
    echo Warning: get_results.py not found.
)

:: Check if rebuild_images.py exists and run it
IF EXIST "%CURR_DIR%\rebuild_images.py" (
    echo Running rebuild_images.py...
    python "%CURR_DIR%\rebuild_images.py"
    IF %ERRORLEVEL% NEQ 0 (
        echo Error: rebuild_images.py execution failed.
        EXIT /B 1
    )
) ELSE (
    echo Warning: rebuild_images.py not found.
)

ENDLOCAL

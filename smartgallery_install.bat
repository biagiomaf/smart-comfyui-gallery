::An installation bat that:
:: Navigates cmd to the current directory
:: Clones the github repo
:: Navigates to the clone
:: Creates and activates a venv
:: Installs requirements.txt
:: Presents a message displaying smartgallery.py config variables.

@echo off
color 0b
echo.
echo *** STARTING INSTALLATION ***
TIMEOUT /t 1 > null

:: Move to current directory (cmd)
cd /d "%~dp0"

echo *** Cloning project from GitHub ***
:: Clone smart-comfyUI-gallery from github
git clone https://github.com/biagiomaf/smart-comfyui-gallery > nul 2>&1

:: Move to sub directory (cmd)
cd smart-comfyui-gallery

echo *** Creating venv ***
:: Create virtual environment
python -m venv venv

echo *** Activating venv ***
:: Activate vitual enviroment
call venv\Scripts\activate

echo *** Installing requirements.txt ***
:: Install requirements.txt
pip install -r requirements.txt > nul 2>&1

echo *** INSTALLATION COMPLETE ***
echo.
echo --
echo To finish your configuration update the following paths in smart-comfyui-galley/smartgallery.py
echo --
echo.
echo -ComfyUI folders-
echo 	BASE_OUTPUT_PATH = 'C:/your/path/to/ComfyUI/output'
echo 	BASE_INPUT_PATH = 'C:/your/path/to/ComfyUI/input'
echo.
echo -FFmpeg path- (Optional for video workflow extraction)
echo 	FFPROBE_MANUAL_PATH = "C:/path/to/ffprobe.exe"
echo.
echo -Server port- (different from ComfyUI)
echo 	SERVER_PORT = 8189
echo.
PAUSE


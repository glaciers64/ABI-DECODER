@echo off
title ABI DECODER

echo Activating virtual environment...
call venv\Scripts\activate

echo Starting the bot...
python main.py

echo done

pause
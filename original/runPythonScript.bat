cd src

call D:\3Di64\venv\Scripts\activate.bat
python .\3DiSimulation.py > ..\logs\log.txt 2>&1

cd ..
exit /b
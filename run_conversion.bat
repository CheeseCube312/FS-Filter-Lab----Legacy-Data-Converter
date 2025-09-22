@echo off
REM Install tqdm if not present and run the conversion script
pip install tqdm
python convert_data_format.py
pause

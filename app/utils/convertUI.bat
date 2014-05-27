@echo off
call config.bat
for /f %%f in ('dir /b ..\gui\*.ui') do (
	echo Converting %%~nf.ui
	call %%python%% %%pyuic%% ..\gui\%%~nf.ui --output ..\gui\%%~nf.py
)
@echo off
set OLDDIR=%CD%
cd %~p0
call app\utils\config.bat
call %%python%% app\src\main.py
cd %OLDDIR%

@echo off
set OLDDIR=%CD%
cd %~p0
call utils\config.bat
call %%python%% src\main.py
cd %OLDDIR%
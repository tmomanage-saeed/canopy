@echo off
cd /d "%~dp0"
title Aa_Canopy Dashboard Server

echo Starting server on http://localhost:8080 ...
start "" python serve_dashboard.py

timeout /t 2 /nobreak >nul

start "" http://localhost:8080/KPI_Report_Template.html
start "" http://localhost:8080/Overview_Dashboard.html
start "" http://localhost:8080/Trees_Shrubs_KPI.html
start "" http://localhost:8080/existing_trees_dashboard.html
start "" http://localhost:8080/KPI_Dashboard.html

echo.
echo All dashboards opened in your browser.
echo Keep the "serve_dashboard.py" window open in the background - closing it stops the server.
echo This window can be closed.
timeout /t 5 >nul

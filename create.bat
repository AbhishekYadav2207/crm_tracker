@echo off
SET ROOT=frontend_v2

echo Creating project structure for %ROOT%...

:: Create directories
mkdir %ROOT%
mkdir %ROOT%\css
mkdir %ROOT%\js

:: Create empty files
type nul > %ROOT%\index.html
type nul > %ROOT%\css\style.css
type nul > %ROOT%\js\app.js
type nul > %ROOT%\js\api.js
type nul > %ROOT%\js\auth.js
type nul > %ROOT%\js\components.js

echo Project structure created successfully!
pause
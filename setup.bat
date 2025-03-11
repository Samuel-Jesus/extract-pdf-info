@echo off
echo Criando ambiente virtual...
python -m venv venv

echo Ativando ambiente virtual...
call venv\Scripts\activate.bat

echo Instalando dependencias...
pip install -r requirements.txt

echo Instalacao concluida!
echo Para iniciar a API, execute: python run.py
echo.
echo Lembre-se de instalar o Tesseract OCR para que a funcionalidade de OCR funcione corretamente.
echo Baixe em: https://github.com/UB-Mannheim/tesseract/wiki
echo.
pause 
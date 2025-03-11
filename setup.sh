#!/bin/bash

echo "Criando ambiente virtual..."
python3 -m venv venv

echo "Ativando ambiente virtual..."
source venv/bin/activate

echo "Instalando dependências..."
pip install -r requirements.txt

echo "Instalação concluída!"
echo "Para iniciar a API, execute: python run.py"
echo ""
echo "Lembre-se de instalar o Tesseract OCR para que a funcionalidade de OCR funcione corretamente."
echo "Linux: sudo apt-get install tesseract-ocr"
echo "Mac: brew install tesseract"
echo "" 
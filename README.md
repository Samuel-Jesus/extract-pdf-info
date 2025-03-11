# API Python para Extração de PDF

Uma API simples construída com FastAPI para extrair texto de arquivos PDF.

## Requisitos

- Python 3.8+
- Dependências listadas em `requirements.txt`
- Tesseract OCR (para reconhecimento de texto em imagens)

## Instalação

1. Clone o repositório
2. Crie um ambiente virtual:
   ```
   python -m venv venv
   ```
3. Ative o ambiente virtual:
   - Windows:
     ```
     venv\Scripts\activate
     ```
   - Linux/Mac:
     ```
     source venv/bin/activate
     ```
4. Instale as dependências:
   ```
   pip install -r requirements.txt
   ```

5. Instale o Tesseract OCR:
   - Windows:
     1. Baixe o instalador em: https://github.com/UB-Mannheim/tesseract/wiki
     2. Instale com as opções padrão
     3. Adicione o diretório de instalação (ex: `C:\Program Files\Tesseract-OCR`) ao PATH do sistema
   
   - Linux:
     ```
     sudo apt-get install tesseract-ocr
     ```
   
   - Mac:
     ```
     brew install tesseract
     ```

## Executando a API

Para iniciar o servidor de desenvolvimento:

```
uvicorn app.main:app --reload
```

Ou use o script de execução:

```
python run.py
```

A API estará disponível em `http://localhost:8000`

## Documentação

A documentação interativa da API estará disponível em:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Endpoints

- `GET /`: Endpoint raiz que retorna uma mensagem de boas-vindas
- `POST /extract-text`: Extrai texto de um arquivo PDF enviado como upload
- `POST /extract-text-base64`: Extrai texto de um arquivo PDF enviado como string base64
- `GET /health`: Verificação de saúde da API

## Como usar a API

### Método 1: Upload de Arquivo

#### Exemplo com curl

```bash
curl -X POST "http://localhost:8000/extract-text" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@caminho/para/seu/arquivo.pdf"
```

#### Exemplo com Python

```python
import requests

url = "http://localhost:8000/extract-text"
files = {"file": open("caminho/para/seu/arquivo.pdf", "rb")}

response = requests.post(url, files=files)
print(response.json())
```

### Método 2: Envio em Base64

#### Exemplo com curl

```bash
curl -X POST "http://localhost:8000/extract-text-base64" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{
    "file_base64": "JVBERi0xLjMKJcTl8uXrp...",
    "filename": "documento.pdf"
  }'
```

#### Exemplo com Python

```python
import requests
import base64

url = "http://localhost:8000/extract-text-base64"

# Ler o arquivo PDF e convertê-lo para base64
with open("caminho/para/seu/arquivo.pdf", "rb") as pdf_file:
    pdf_base64 = base64.b64encode(pdf_file.read()).decode('utf-8')

payload = {
    "file_base64": pdf_base64,
    "filename": "documento.pdf"  # Opcional
}

response = requests.post(url, json=payload)
print(response.json())
```

## Resposta da API

### Resposta de Sucesso

A API retorna um JSON com o texto extraído do PDF:

```json
{
  "extracted_text": "Texto extraído do PDF...",
  "page_count": 5,
  "filename": "documento.pdf"
}
```

### Resposta com Aviso

Se nenhum texto for extraído, a API retornará:

```json
{
  "warning": "Nenhum texto foi extraído do PDF. O documento pode estar vazio, protegido ou conter apenas imagens que não puderam ser processadas pelo OCR.",
  "extracted_text": "",
  "page_count": 5,
  "filename": "documento.pdf"
}
```

### Resposta de Erro

Em caso de erro, a API retorna um JSON com informações detalhadas:

```json
{
  "error": true,
  "error_code": "CÓDIGO_DO_ERRO",
  "message": "Descrição do erro",
  "details": {
    "campo1": "valor1",
    "campo2": "valor2"
  }
}
```

## Códigos de Status HTTP

A API utiliza os seguintes códigos de status HTTP:

- `200 OK`: Requisição bem-sucedida
- `400 Bad Request`: Erro no cliente (arquivo inválido, formato incorreto, etc.)
- `500 Internal Server Error`: Erro no servidor

## Códigos de Erro

| Código de Erro | Descrição | Status HTTP |
|----------------|-----------|-------------|
| `FILE_NOT_PROVIDED` | Nenhum arquivo foi fornecido | 400 |
| `INVALID_FILE_TYPE` | O arquivo não é um PDF | 400 |
| `EMPTY_FILE` | O arquivo está vazio | 400 |
| `FILE_READ_ERROR` | Erro ao ler o arquivo | 400 |
| `INVALID_PDF` | O arquivo fornecido não é um PDF válido | 400 |
| `INVALID_BASE64` | O conteúdo base64 fornecido é inválido | 400 |
| `EMPTY_PDF` | O PDF não contém páginas | 400 |
| `PDF_PROTECTED` | O PDF está protegido por senha | 400 |
| `PDF_PROCESSING_ERROR` | Erro ao processar o PDF | 500 |
| `TESSERACT_NOT_FOUND` | Tesseract OCR não está instalado ou não está no PATH | 500 |
| `UNEXPECTED_ERROR` | Erro inesperado | 500 |

## Integração com n8n

Para consumir esta API no n8n, você pode usar um dos dois métodos:

### Método 1: Upload de Arquivo

1. Adicione um nó HTTP Request
2. Configure o nó:
   - **Method**: POST
   - **URL**: http://localhost:8000/extract-text
   - **Authentication**: None
   - **Request Format**: Form-Data/Multipart
   - **Binary Data**: Ative esta opção
   - **Binary Property**: data (ou o nome da propriedade que contém o arquivo PDF)
   - **Form-Data/Multipart Parameters**:
     - Adicione um parâmetro:
       - **Name**: file
       - **Value**: =data (ou o nome da propriedade que contém o arquivo PDF)
       - **Type**: File

### Método 2: Envio em Base64 (Recomendado)

1. Adicione um nó HTTP Request
2. Configure o nó:
   - **Method**: POST
   - **URL**: http://localhost:8000/extract-text-base64
   - **Authentication**: None
   - **Request Format**: JSON
   - **JSON/RAW Parameters**:
     ```json
     {
       "file_base64": "={{$binary.data.base64}}",
       "filename": "={{$binary.data.fileName}}"
     }
     ```

### Processamento da Resposta

Adicione um nó Function para tratar a resposta:

```javascript
// Verificar se houve erro
if (items[0].json.error) {
  // Tratar erro
  return {
    json: {
      success: false,
      error: items[0].json.error_code,
      message: items[0].json.message,
      details: items[0].json.details
    }
  };
}

// Tratar sucesso
return {
  json: {
    success: true,
    text: items[0].json.extracted_text,
    pageCount: items[0].json.page_count,
    filename: items[0].json.filename,
    warning: items[0].json.warning || null
  }
};
```

### Exemplo de Fluxo de Trabalho Completo (Base64)

```json
{
  "nodes": [
    {
      "parameters": {
        "url": "http://localhost:8000/extract-text-base64",
        "authentication": "none",
        "method": "POST",
        "sendHeaders": true,
        "headerParameters": {
          "parameters": [
            {
              "name": "Content-Type",
              "value": "application/json"
            }
          ]
        },
        "options": {},
        "sendBody": true,
        "bodyParameters": {
          "parameters": [
            {
              "name": "file_base64",
              "value": "={{$binary.data.base64}}"
            },
            {
              "name": "filename",
              "value": "={{$binary.data.fileName}}"
            }
          ]
        }
      },
      "name": "Extract PDF Text",
      "type": "n8n-nodes-base.httpRequest",
      "typeVersion": 2,
      "position": [650, 300]
    },
    {
      "parameters": {
        "functionCode": "// Verificar se houve erro\nif (items[0].json.error) {\n  // Tratar erro\n  return {\n    json: {\n      success: false,\n      error: items[0].json.error_code,\n      message: items[0].json.message,\n      details: items[0].json.details\n    }\n  };\n}\n\n// Tratar sucesso\nreturn {\n  json: {\n    success: true,\n    text: items[0].json.extracted_text,\n    pageCount: items[0].json.page_count,\n    filename: items[0].json.filename,\n    warning: items[0].json.warning || null\n  }\n};"
      },
      "name": "Process Response",
      "type": "n8n-nodes-base.function",
      "typeVersion": 1,
      "position": [850, 300]
    }
  ],
  "connections": {
    "Extract PDF Text": {
      "main": [
        [
          {
            "node": "Process Response",
            "type": "main",
            "index": 0
          }
        ]
      ]
    }
  }
}
```

## Tratamento de Erros no n8n

Para lidar com erros de forma adequada no n8n, você pode adicionar um nó IF após o nó HTTP Request:

```
IF [Item: 0] > [JSON] > error EXISTS
```

Em seguida, adicione um nó Error para o caminho "true" (quando há erro):

```
Error: =Erro na extração de PDF: {{$json["message"]}} (Código: {{$json["error_code"]}})
```

Isso garantirá que o fluxo de trabalho seja interrompido com uma mensagem de erro clara quando a API retornar um erro. 
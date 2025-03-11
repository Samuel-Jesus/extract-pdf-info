from fastapi import FastAPI, UploadFile, File, HTTPException, status, Body, Form, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
import fitz  # PyMuPDF para extrair texto
import pytesseract  # OCR para PDFs baseados em imagens
from PIL import Image
import io
import os
import traceback
from typing import Dict, Any, Optional, Union
import base64
from pydantic import BaseModel, Field

app = FastAPI(
    title="API de Extração de PDF",
    description="API para extrair texto de arquivos PDF",
    version="1.0.0"
)

# Verificar se o diretório static existe
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    # Montar os arquivos estáticos
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

class APIError(Exception):
    """Classe personalizada para erros da API"""
    def __init__(self, status_code: int, error_code: str, message: str, details: Optional[Dict[str, Any]] = None):
        self.status_code = status_code
        self.error_code = error_code
        self.message = message
        self.details = details or {}
        super().__init__(self.message)

@app.exception_handler(APIError)
async def api_error_handler(request, exc: APIError):
    """Manipulador de exceções para erros da API"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "error_code": exc.error_code,
            "message": exc.message,
            "details": exc.details
        }
    )

# Modelo para receber PDF em base64
class PDFBase64Request(BaseModel):
    file_base64: str = Field(..., description="Conteúdo do PDF em formato base64")
    filename: Optional[str] = Field(None, description="Nome do arquivo (opcional)")

def extract_text_from_pdf(pdf_bytes) -> Dict[str, Any]:
    """
    Extrai texto de um arquivo PDF.
    
    Args:
        pdf_bytes: Bytes do arquivo PDF
        
    Returns:
        Dicionário com o texto extraído ou mensagem de erro
        
    Raises:
        APIError: Se ocorrer um erro durante a extração
    """
    try:
        # Verificar se o Tesseract está instalado
        try:
            pytesseract.get_tesseract_version()
        except pytesseract.TesseractNotFoundError:
            raise APIError(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                error_code="TESSERACT_NOT_FOUND",
                message="Tesseract OCR não está instalado ou não está no PATH",
                details={
                    "solution": "Instale o Tesseract OCR e adicione-o ao PATH. Veja o README para mais informações."
                }
            )
        
        # Verificar se o PDF é válido
        try:
            doc = fitz.open("pdf", pdf_bytes)
        except Exception as e:
            raise APIError(
                status_code=status.HTTP_400_BAD_REQUEST,
                error_code="INVALID_PDF",
                message="O arquivo fornecido não é um PDF válido",
                details={
                    "original_error": str(e)
                }
            )
        
        # Extrair texto
        text = ""
        page_count = len(doc)
        
        if page_count == 0:
            raise APIError(
                status_code=status.HTTP_400_BAD_REQUEST,
                error_code="EMPTY_PDF",
                message="O PDF não contém páginas",
                details={}
            )
        
        for page_num, page in enumerate(doc):
            page_text = page.get_text("text")
            text += page_text
            
            # Se o texto estiver vazio, tente extrair como imagem usando OCR
            if not page_text.strip():
                try:
                    pix = page.get_pixmap()
                    img_data = pix.tobytes("png")
                    img = Image.open(io.BytesIO(img_data))
                    ocr_text = pytesseract.image_to_string(img)
                    text += ocr_text
                except Exception as e:
                    # Continuar mesmo se o OCR falhar em uma página
                    pass
        
        # Verificar se algum texto foi extraído
        if not text.strip():
            return {
                "warning": "Nenhum texto foi extraído do PDF. O documento pode estar vazio, protegido ou conter apenas imagens que não puderam ser processadas pelo OCR.",
                "extracted_text": "",
                "page_count": page_count
            }
        
        return {
            "extracted_text": text.strip(),
            "page_count": page_count
        }
    
    except APIError:
        # Re-lançar APIErrors para serem tratados pelo manipulador
        raise
    except Exception as e:
        # Capturar o traceback para debugging
        error_traceback = traceback.format_exc()
        
        # Determinar o tipo de erro
        if "password" in str(e).lower():
            raise APIError(
                status_code=status.HTTP_400_BAD_REQUEST,
                error_code="PDF_PROTECTED",
                message="O PDF está protegido por senha",
                details={
                    "original_error": str(e)
                }
            )
        else:
            raise APIError(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                error_code="PDF_PROCESSING_ERROR",
                message=f"Erro ao processar o PDF: {str(e)}",
                details={
                    "traceback": error_traceback
                }
            )
    finally:
        # Garantir que o documento seja fechado
        if 'doc' in locals():
            doc.close()

# Função para processar o PDF e retornar o resultado
async def process_pdf(pdf_bytes: bytes, filename: Optional[str] = None) -> Dict[str, Any]:
    """
    Processa um PDF e retorna o texto extraído.
    
    Args:
        pdf_bytes: Bytes do arquivo PDF
        filename: Nome do arquivo (opcional)
        
    Returns:
        Dicionário com o texto extraído e metadados
    """
    # Verificar se o arquivo está vazio
    if len(pdf_bytes) == 0:
        raise APIError(
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code="EMPTY_FILE",
            message="O arquivo está vazio",
            details={}
        )
    
    # Extrair texto do PDF
    result = extract_text_from_pdf(pdf_bytes)
    
    # Adicionar informações do arquivo à resposta
    if filename:
        result["filename"] = filename
    
    return result

@app.post("/extract-text", status_code=status.HTTP_200_OK)
async def extract_text(file: Optional[UploadFile] = File(None)):
    """
    Extrai texto de um arquivo PDF enviado como upload.
    
    Args:
        file: Arquivo PDF para extrair o texto
    
    Returns:
        JSON com o texto extraído ou mensagem de erro
    
    Raises:
        HTTPException: Se ocorrer um erro durante o processamento
    """
    # Verificar se o arquivo foi fornecido
    if not file:
        raise APIError(
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code="FILE_NOT_PROVIDED",
            message="Nenhum arquivo foi fornecido",
            details={}
        )
    
    # Verificar se o arquivo é um PDF
    if not file.filename.lower().endswith('.pdf'):
        raise APIError(
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code="INVALID_FILE_TYPE",
            message="O arquivo deve ser um PDF",
            details={
                "provided_file": file.filename,
                "content_type": file.content_type
            }
        )
    
    try:
        # Ler o arquivo
        try:
            pdf_bytes = await file.read()
        except Exception as e:
            raise APIError(
                status_code=status.HTTP_400_BAD_REQUEST,
                error_code="FILE_READ_ERROR",
                message="Erro ao ler o arquivo",
                details={
                    "original_error": str(e)
                }
            )
        
        # Processar o PDF
        result = await process_pdf(pdf_bytes, file.filename)
        
        return result
    
    except APIError:
        # Re-lançar APIErrors para serem tratados pelo manipulador
        raise
    except Exception as e:
        # Capturar erros não tratados
        error_traceback = traceback.format_exc()
        raise APIError(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code="UNEXPECTED_ERROR",
            message=f"Erro inesperado: {str(e)}",
            details={
                "traceback": error_traceback
            }
        )

@app.post("/extract-text-base64", status_code=status.HTTP_200_OK)
async def extract_text_base64(request: PDFBase64Request):
    """
    Extrai texto de um arquivo PDF enviado como string base64.
    
    Args:
        request: Objeto contendo o PDF em formato base64 e opcionalmente o nome do arquivo
    
    Returns:
        JSON com o texto extraído ou mensagem de erro
    
    Raises:
        HTTPException: Se ocorrer um erro durante o processamento
    """
    try:
        # Decodificar o PDF de base64 para bytes
        try:
            # Remover possíveis prefixos de data URI
            base64_data = request.file_base64
            if "," in base64_data:
                base64_data = base64_data.split(",", 1)[1]
            
            pdf_bytes = base64.b64decode(base64_data)
        except Exception as e:
            raise APIError(
                status_code=status.HTTP_400_BAD_REQUEST,
                error_code="INVALID_BASE64",
                message="O conteúdo base64 fornecido é inválido",
                details={
                    "original_error": str(e)
                }
            )
        
        # Processar o PDF
        filename = request.filename or "documento.pdf"
        result = await process_pdf(pdf_bytes, filename)
        
        return result
    
    except APIError:
        # Re-lançar APIErrors para serem tratados pelo manipulador
        raise
    except Exception as e:
        # Capturar erros não tratados
        error_traceback = traceback.format_exc()
        raise APIError(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code="UNEXPECTED_ERROR",
            message=f"Erro inesperado: {str(e)}",
            details={
                "traceback": error_traceback
            }
        )

@app.get("/", response_class=HTMLResponse)
async def read_root():
    """
    Endpoint raiz da API.
    
    Redireciona para a interface web.
    """
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <meta http-equiv="refresh" content="0; url=/static/index.html">
        <title>Redirecionando...</title>
    </head>
    <body>
        <p>Redirecionando para a interface web...</p>
    </body>
    </html>
    """

@app.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    """
    Verificação de saúde da API.
    
    Retorna o status da API e verifica se o Tesseract está instalado.
    """
    tesseract_status = "available"
    tesseract_version = None
    
    try:
        tesseract_version = pytesseract.get_tesseract_version()
    except Exception:
        tesseract_status = "unavailable"
    
    return {
        "status": "healthy",
        "api_version": "1.0.0",
        "tesseract_status": tesseract_status,
        "tesseract_version": tesseract_version
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True) 
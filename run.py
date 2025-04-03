import uvicorn
import os

if __name__ == "__main__":
    # Detecta se está em ambiente de produção (valor padrão é desenvolvimento)
    is_dev = os.environ.get("NODE_ENV", "development") == "development"
    
    # Em desenvolvimento utiliza o parâmetro reload=True para hot-reload
    # Em produção desabilita o reload para melhor performance
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=is_dev) 
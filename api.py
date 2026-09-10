from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from orquestrador.orquestrador import (
    carregar_config,
    criar_tarefa,
    executar_pipeline
)

app = FastAPI(title="Business Hunter API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)


@app.post("/executar")
def executar():
    """
    Roda o pipeline completo (Hunter -> Filtro -> Arquiteto -> Planilha)
    e retorna o resultado. Isso pode demorar alguns minutos, dependendo
    da quantidade de empresas configurada em config/config.yaml.
    """

    try:
        config = carregar_config()
        tarefa = criar_tarefa(config)
        resultado = executar_pipeline(tarefa)

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error)
        )

    return resultado


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000
    )

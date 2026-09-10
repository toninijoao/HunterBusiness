from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from orquestrador.orquestrador import (
    carregar_config,
    criar_tarefa,
    executar_pipeline
)

app = FastAPI(title="Business Hunter API")

# Libera acesso do frontend local (Vite roda em portas 5173/4173
# por padrão). Como é uma ferramenta pessoal rodando na sua própria
# máquina, liberar geral é suficiente e mais simples.
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
        resultado = executar_pipeline(
            tarefa,
            segmentos=config.get("segmentos")
        )

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

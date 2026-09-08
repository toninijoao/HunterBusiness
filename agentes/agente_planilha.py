import json
from pathlib import Path

from dotenv import load_dotenv
from ollama import chat


load_dotenv()

model = "qwen3:8b"

base_dir = Path(__file__).resolve().parent.parent


def carregar_prompt() -> str:
    caminho = base_dir / "prompts" / "planilha.md"

    return caminho.read_text(encoding="utf-8")


def carregar_schema() -> dict:
    caminho = base_dir / "schemas" / "planilha.json"

    with caminho.open("r", encoding="utf-8") as arquivo:
        return json.load(arquivo)


def executar_planilha(
    empresa: dict,
    perfil: dict,
    solucao: dict
) -> dict:

    system_prompt = carregar_prompt()
    schema = carregar_schema()

    tarefa = f"""
Organize os dados abaixo para a planilha.

DADOS DA EMPRESA:
{json.dumps(empresa, ensure_ascii=False, indent=2)}

PERFIL DO NEGÓCIO:
{json.dumps(perfil, ensure_ascii=False, indent=2)}

SOLUÇÃO RECOMENDADA:
{json.dumps(solucao, ensure_ascii=False, indent=2)}
"""

    response = chat(
        model=model,
        messages=[
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": tarefa
            }
        ],
        format=schema
    )

    return extrair_resultado(response)


def extrair_resultado(response) -> dict:

    conteudo = response.message.content

    if not conteudo:
        raise ValueError(
            "O agente planilha não retornou nenhum resultado."
        )

    try:
        return json.loads(conteudo)

    except json.JSONDecodeError as error:
        raise ValueError(
            f"O agente planilha retornou um JSON inválido: {error}"
        )
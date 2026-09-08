import json
from pathlib import Path

from dotenv import load_dotenv
from ollama import chat


load_dotenv()

model = "qwen3:8b"

base_dir = Path(__file__).resolve().parent.parent


def carregar_prompt() -> str:
    caminho = base_dir / "prompts" / "arquiteto.md"

    return caminho.read_text(encoding="utf-8")


def carregar_schema() -> dict:
    caminho = base_dir / "schemas" / "solucao.json"

    with caminho.open("r", encoding="utf-8") as arquivo:
        return json.load(arquivo)


def executar_arquiteto(perfil: dict) -> dict:

    system_prompt = carregar_prompt()
    schema = carregar_schema()

    tarefa = f"""
Analise o perfil de negócio abaixo e determine a solução digital
mais adequada para essa empresa.

PERFIL DO NEGÓCIO:
{json.dumps(perfil, ensure_ascii=False, indent=2)}
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

    if not response.message.content:
        raise ValueError(
            "O agente arquiteto não retornou nenhum resultado."
        )

    return json.loads(response.message.content)
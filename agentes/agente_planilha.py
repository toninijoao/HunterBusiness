import json
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types


load_dotenv()

client = genai.Client()
model = "gemini-2.5-flash-lite"

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

    response = client.models.generate_content(
        model=model,
        contents=tarefa,
        config=types.GenerateContentConfig(
            system_instruction=system_prompt,
            response_mime_type="application/json",
            response_schema=schema
        )
    )

    return extrair_resultado(response)


def extrair_resultado(response) -> dict:

    if not response.text:
        raise ValueError(
            "O agente planilha não retornou nenhum resultado."
        )

    return json.loads(response.text)
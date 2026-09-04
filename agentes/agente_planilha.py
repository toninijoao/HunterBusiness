import json
from pathlib import Path
from google import genai

client = genai.Client()
model = "gemini-2.5-flash-lite"
base_dir = Path(__file__).resolve().parent.parent

def carregar_prompt() -> str:
    caminho = base_dir / "prompts" / "planilha.md"

    return caminho.read_text(encoding="utf-8")

def executar_planilha(empresa: dict, perfil: dict, solucao: dict) -> dict:
    system_prompt = carregar_prompt()

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
        max_tokens=5000,
        system=system_prompt,
        messages=[
            {
                "role": "user",
                "content": tarefa
            }
        ]
    )

    return extrair_resultado(response)

def extrair_resultado(response) -> dict:
    textos = [
        block.text
        for block in response.content
        if block.type == "text"
    ]

    if not textos:
        raise ValueError(
            "O agente planilha não retornou um resultado textual."
        )

    texto = "\n".join(textos)

    return json.loads(texto)
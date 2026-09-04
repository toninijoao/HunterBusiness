import json
from pathlib import Path
from google import genai

client = genai.Client()
model = "gemini-2.5-flash-lite"

base_dir = Path(__file__).resolve().parent.parent

def carregar_prompt() -> str:
    prompt_path = base_dir / "prompts" / "arquiteto.md"

    return prompt_path.read_text(encoding="utf-8")

def carregar_schema() -> dict:
    schema_path = base_dir / "schemas" / "solucao.json"

    with schema_path.open("r", encoding="utf-8") as file:
        return json.load(file)

def executar_arquiteto(perfil: dict) -> dict:
    system_prompt = carregar_prompt()
    schema = carregar_schema()

    response = client.messages.create(
        model=model,
        max_tokens=5000,
        system=system_prompt,
        messages=[
            {
                "role": "user",
                "content": (
                    "Analise o seguinte perfil de empresa e desenvolva digital mais adequada.\n\n"
                    f"{json.dumps(perfil, ensure_ascii=False, indent=2)}"
                ),
            }
        ],
    )

    resposta_texto = response.content[0].text

    return json.loads(resposta_texto)
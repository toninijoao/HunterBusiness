import json
from pathlib import Path

from dotenv import load_dotenv
from ollama import chat

from tools.pesquisa_web import pesquisar_web, pesquisar_web_tool
from tools.mapeador import mapear_endereco, mapear_endereco_tool


load_dotenv()

model = "qwen3:8b"

base_dir = Path(__file__).resolve().parent.parent


def carregar_prompt() -> str:
    caminho = base_dir / "prompts" / "perfil.md"

    return caminho.read_text(encoding="utf-8")


def carregar_schema() -> dict:
    caminho = base_dir / "schemas" / "perfil.json"

    with caminho.open("r", encoding="utf-8") as arquivo:
        return json.load(arquivo)


tools = [
    pesquisar_web,
    mapear_endereco
]


tool_functions = {
    "pesquisar_web": pesquisar_web,
    "mapear_endereco": mapear_endereco
}


def executar_tool(nome: str, argumentos: dict):
    if nome not in tool_functions:
        raise ValueError(
            f"Ferramenta desconhecida: {nome}"
        )

    return tool_functions[nome](**argumentos)


def executar_filtro(empresa: dict) -> dict:

    system_prompt = carregar_prompt()
    schema = carregar_schema()

    tarefa = f"""
Construa o perfil de negócio da empresa abaixo.

Empresa:
{json.dumps(empresa, ensure_ascii=False, indent=2)}
"""

    messages = [
        {
            "role": "system",
            "content": system_prompt
        },
        {
            "role": "user",
            "content": tarefa
        }
    ]

    while True:

        response = chat(
            model=model,
            messages=messages,
            tools=tools
        )

        messages.append(response.message)

        if not response.message.tool_calls:
            break

        for tool_call in response.message.tool_calls:

            try:
                resultado = executar_tool(
                    tool_call.function.name,
                    tool_call.function.arguments
                )

                messages.append(
                    {
                        "role": "tool",
                        "tool_name": tool_call.function.name,
                        "content": json.dumps(
                            resultado,
                            ensure_ascii=False
                        )
                    }
                )

            except Exception as error:

                messages.append(
                    {
                        "role": "tool",
                        "tool_name": tool_call.function.name,
                        "content": json.dumps(
                            {
                                "error": str(error)
                            },
                            ensure_ascii=False
                        )
                    }
                )

    return extrair_resultado(response, schema)


def extrair_resultado(response, schema: dict) -> dict:

    conteudo = response.message.content

    if not conteudo:
        raise ValueError(
            "O agente filtro não retornou nenhum resultado."
        )

    try:
        return json.loads(conteudo)

    except json.JSONDecodeError as error:
        raise ValueError(
            f"O agente filtro retornou um JSON inválido: {error}"
        )
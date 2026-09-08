import json
from pathlib import Path

from dotenv import load_dotenv
from ollama import chat

from tools.registro import tools, tool_functions


load_dotenv()

model = "qwen3:8b"

base_dir = Path(__file__).resolve().parent.parent


def carregar_prompt() -> str:
    caminho = base_dir / "prompts" / "descoberta.md"

    return caminho.read_text(encoding="utf-8")


def carregar_schema() -> dict:
    caminho = base_dir / "schemas" / "empresa.json"

    with caminho.open("r", encoding="utf-8") as arquivo:
        return json.load(arquivo)


def executar_tool(nome: str, argumentos: dict):

    if nome not in tool_functions:
        raise ValueError(
            f"Ferramenta desconhecida: {nome}"
        )

    funcao = tool_functions[nome]

    return funcao(**argumentos)


def executar_hunter(tarefa: str) -> dict:

    system_prompt = carregar_prompt()

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

            nome_tool = tool_call.function.name
            argumentos = tool_call.function.arguments

            try:

                resultado = executar_tool(
                    nome_tool,
                    argumentos
                )

                messages.append(
                    {
                        "role": "tool",
                        "tool_name": nome_tool,
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
                        "tool_name": nome_tool,
                        "content": json.dumps(
                            {
                                "error": str(error)
                            },
                            ensure_ascii=False
                        )
                    }
                )

    conteudo_final = response.message.content

    if not conteudo_final:
        raise ValueError(
            "O Hunter não retornou nenhuma decisão final."
        )

    schema = carregar_schema()

    mensagens_finais = messages + [
        {
            "role": "user",
            "content": (
                "Agora finalize a tarefa. "
                "Retorne exclusivamente o resultado final "
                "compatível com o schema fornecido. "
                "Não escreva explicações fora do JSON. "
                "Empresas rejeitadas não devem aparecer. "
                "O campo 'empresas' deve conter somente empresas "
                "efetivamente validadas."
            )
        }
    ]

    resposta_final = chat(
        model=model,
        messages=mensagens_finais,
        format=schema
    )

    return extrair_resultado(resposta_final)


def extrair_resultado(response) -> dict:

    conteudo = response.message.content

    if not conteudo:
        raise ValueError(
            "O Hunter não retornou nenhum resultado."
        )

    try:
        resultado = json.loads(conteudo)

    except json.JSONDecodeError as error:
        raise ValueError(
            f"O Hunter retornou um JSON inválido: {error}"
        )

    if not isinstance(resultado, dict):
        raise ValueError(
            "O resultado do Hunter deve ser um objeto JSON."
        )

    if "empresas" not in resultado:
        raise ValueError(
            "O resultado do Hunter não possui o campo 'empresas'."
        )

    if not isinstance(resultado["empresas"], list):
        raise ValueError(
            "O campo 'empresas' deve ser uma lista."
        )

    return resultado
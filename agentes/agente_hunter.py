import json
from pathlib import Path
from anthropic import Anthropic
from tools.registro import tools, tool_functions


client = Anthropic()
model="claude-sonnet-4-6"
base_dir = Path(__file__).resolve().parent.parent

def carregar_prompt() -> str:
    caminho = base_dir / "prompts" / "descoberta.md"

    return caminho.read_text(encoding="utf-8")

def executar_tool(nome: str, argumentos: dict):
    if nome not in tool_functions:
        raise ValueError(f"Ferramenta desconhecida: {nome}")

    funcao = tool_functions[nome]

    return funcao(**argumentos)

def executar_hunter(tarefa: str) -> dict:
    system_prompt = carregar_prompt()
    messages = [
        {
            "role": "user",
            "content": tarefa
        }
    ]

    while True:
        response = client.messages.create(
            model=model,
            max_tokens=5000,
            system=system_prompt,
            tools=tools,
            messages=messages
        )

        messages.append(
            {
                "role": "assistant",
                "content": response.content
            }
        )

        if response.stop_reason == "end_turn":
            break

        if response.stop_reason != "tool_use":
            raise RuntimeError(
                f"Execução interrompida: {response.stop_reason}"
            )

        tool_results = []

        for block in response.content:

            if block.type != "tool_use":
                continue

            try:
                result = executar_tool(
                    block.name,
                    block.input
                )

                tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": json.dumps(
                            result,
                            ensure_ascii=False
                        )
                    }
                )

            except Exception as error:

                tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": json.dumps(
                            {
                                "error": str(error)
                            },
                            ensure_ascii=False
                        ),
                        "is_error": True
                    }
                )

            if tool_results:
                messages.append(
                    {
                        "role": "user",
                        "content": tool_results
                    }
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
            "O hunter não retornou um resultado textual."
        )

    texto = "\n".join(textos)

    return json.loads(texto)
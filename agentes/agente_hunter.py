import json
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types

from tools.registro import tools, tool_functions


load_dotenv()

client = genai.Client()

model = "gemini-2.5-flash-lite"

base_dir = Path(__file__).resolve().parent.parent


def carregar_prompt() -> str:
    caminho = base_dir / "prompts" / "descoberta.md"

    return caminho.read_text(encoding="utf-8")


def converter_tools() -> list:
    ferramentas = []

    for tool in tools:
        ferramentas.append(
            types.FunctionDeclaration(
                name=tool["name"],
                description=tool["description"],
                parameters=tool["input_schema"]
            )
        )

    return [
        types.Tool(
            function_declarations=ferramentas
        )
    ]


def executar_tool(nome: str, argumentos: dict):
    if nome not in tool_functions:
        raise ValueError(
            f"Ferramenta desconhecida: {nome}"
        )

    funcao = tool_functions[nome]

    return funcao(**argumentos)


def executar_hunter(tarefa: str) -> dict:
    system_prompt = carregar_prompt()

    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_text(text=tarefa)
            ]
        )
    ]

    config = types.GenerateContentConfig(
        system_instruction=system_prompt,
        tools=converter_tools()
    )

    while True:

        response = client.models.generate_content(
            model=model,
            contents=contents,
            config=config
        )

        model_content = response.candidates[0].content

        contents.append(model_content)

        function_calls = [
            part.function_call
            for part in model_content.parts
            if part.function_call
        ]

        if not function_calls:
            break

        function_response_parts = []

        for function_call in function_calls:

            try:
                resultado = executar_tool(
                    function_call.name,
                    dict(function_call.args)
                )

                function_response_parts.append(
                    types.Part.from_function_response(
                        name=function_call.name,
                        response={
                            "result": resultado
                        },
                        id=function_call.id
                    )
                )

            except Exception as error:

                function_response_parts.append(
                    types.Part.from_function_response(
                        name=function_call.name,
                        response={
                            "error": str(error)
                        },
                        id=function_call.id
                    )
                )

        contents.append(
            types.Content(
                role="user",
                parts=function_response_parts
            )
        )

    return extrair_resultado(response)


def extrair_resultado(response) -> dict:

    if not response.text:
        raise ValueError(
            "O Hunter não retornou nenhum resultado."
        )

    return json.loads(response.text)
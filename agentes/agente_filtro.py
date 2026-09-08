import json
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types

from tools.pesquisa_web import pesquisar_web, pesquisar_web_tool
from tools.mapeador import mapear_endereco, mapear_endereco_tool


load_dotenv()

client = genai.Client()

model = "gemini-3.5-flash-lite"

base_dir = Path(__file__).resolve().parent.parent


def carregar_prompt() -> str:
    caminho = base_dir / "prompts" / "perfil.md"

    return caminho.read_text(encoding="utf-8")


def carregar_schema() -> dict:
    caminho = base_dir / "schemas" / "perfil.json"

    with caminho.open("r", encoding="utf-8") as arquivo:
        return json.load(arquivo)


def converter_tools() -> list:
    return [
        types.Tool(
            function_declarations=[
                types.FunctionDeclaration(
                    name=pesquisar_web_tool["name"],
                    description=pesquisar_web_tool["description"],
                    parameters=pesquisar_web_tool["input_schema"]
                ),
                types.FunctionDeclaration(
                    name=mapear_endereco_tool["name"],
                    description=mapear_endereco_tool["description"],
                    parameters=mapear_endereco_tool["input_schema"]
                )
            ]
        )
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
        tools=converter_tools(),
        response_mime_type="application/json",
        response_schema=schema
    )

    while True:

        response = client.models.generate_content(
            model=model,
            contents=contents,
            config=config
        )

        if not response.candidates:
            raise RuntimeError(
                "O Gemini não retornou nenhum candidato."
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
            "O agente filtro não retornou nenhum resultado."
        )

    return json.loads(response.text)
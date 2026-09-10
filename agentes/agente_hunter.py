import json
import re
import unicodedata
from pathlib import Path

from dotenv import load_dotenv
from ollama import chat

from tools.registro import tools, tool_functions


load_dotenv()

model = "qwen3:8b"

base_dir = Path(__file__).resolve().parent.parent

STOPWORDS_SEGMENTO = {"de", "do", "da", "e", "estilo", "empresas"}


def carregar_prompt() -> str:
    caminho = base_dir / "prompts" / "descoberta.md"

    return caminho.read_text(encoding="utf-8")


def carregar_schema() -> dict:
    caminho = base_dir / "schemas" / "empresa.json"

    with caminho.open("r", encoding="utf-8") as arquivo:
        return json.load(arquivo)


def normalizar_texto(texto: str) -> str:

    texto = unicodedata.normalize("NFKD", texto or "")
    texto = texto.encode("ascii", "ignore").decode("ascii")

    return texto.lower()


def representante_segmento(segmento: str) -> str:
    """
    Reduz um segmento configurado (ex: 'estadias(estilo airbnb)',
    'empresas de serviço') a uma palavra-chave representativa
    ('estadias', 'servico'), pra dar pra checar se ele já foi
    pesquisado, sem depender do texto exato que o modelo usar.
    """

    texto = normalizar_texto(segmento)
    palavras = re.findall(r"[a-z0-9]+", texto)
    palavras = [p for p in palavras if p not in STOPWORDS_SEGMENTO]

    return palavras[0] if palavras else texto


def executar_tool(nome: str, argumentos: dict):

    if nome not in tool_functions:
        raise ValueError(
            f"Ferramenta desconhecida: {nome}"
        )

    funcao = tool_functions[nome]

    return funcao(**argumentos)


def executar_hunter(tarefa: str, segmentos: list | None = None) -> dict:

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

    segmentos_pendentes = {
        representante_segmento(segmento): segmento
        for segmento in (segmentos or [])
    }
    segmentos_consultados = set()

    max_iteracoes = 40
    iteracao = 0
    avisos_continuar = 0
    max_avisos_continuar = len(segmentos_pendentes) + 2

    while True:

        iteracao += 1

        if iteracao > max_iteracoes:
            raise RuntimeError(
                "O Hunter atingiu o limite máximo de iterações "
                "sem concluir a tarefa."
            )

        response = chat(
            model=model,
            messages=messages,
            tools=tools
        )

        messages.append(response.message)

        print("\n========================================")
        print(f"ITERAÇÃO {iteracao}")
        print("TOOL_CALLS:", response.message.tool_calls)
        print("CONTENT (resposta do modelo):")
        print(response.message.content)
        print("========================================")

        if response.message.tool_calls:

            for tool_call in response.message.tool_calls:

                nome_tool = tool_call.function.name
                argumentos = tool_call.function.arguments

                print("\n========================================")
                print("TOOL CHAMADA")
                print("Nome:", nome_tool)
                print("Argumentos:", argumentos)
                print("========================================")

                if nome_tool == "pesquisar_web":

                    consulta_normalizada = normalizar_texto(
                        argumentos.get("query", "")
                    )

                    for chave in list(segmentos_pendentes.keys()):
                        if chave in consulta_normalizada:
                            segmentos_consultados.add(chave)

                try:

                    resultado = executar_tool(
                        nome_tool,
                        argumentos
                    )

                    print("\nRESULTADO DA TOOL:")
                    print(
                        json.dumps(
                            resultado,
                            ensure_ascii=False,
                            indent=2
                        )
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

                    print("\nERRO NA TOOL:")
                    print(str(error))

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

            continue

        # O modelo respondeu sem chamar nenhuma ferramenta.
        # Só aceita isso como "terminei" se já tiver ao menos
        # tentado pesquisar todos os segmentos configurados.
        faltando = {
            chave: nome
            for chave, nome in segmentos_pendentes.items()
            if chave not in segmentos_consultados
        }

        if faltando and avisos_continuar < max_avisos_continuar:

            avisos_continuar += 1

            lista_faltando = ", ".join(faltando.values())

            messages.append(
                {
                    "role": "user",
                    "content": (
                        "Você ainda não chamou pesquisar_web para os "
                        f"seguintes segmentos: {lista_faltando}. "
                        "Continue agora mesmo chamando pesquisar_web "
                        "para o próximo desses segmentos em Cornélio "
                        "Procópio, no formato '<segmento> em <cidade>'. "
                        "Não finalize antes de tentar todos."
                    )
                }
            )

            continue

        break

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
                "Finalize a tarefa agora. "
                "Retorne exclusivamente um objeto JSON "
                "compatível com o schema empresa.json. "
                "Inclua somente empresas reais e efetivamente "
                "validadas pelas ferramentas. "
                "Não invente nenhum dado. "
                "Empresas rejeitadas não devem aparecer. "
                "Se nenhuma empresa válida tiver sido encontrada, "
                "retorne {\"empresas\": []}."
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
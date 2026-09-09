import re
import json
import requests


OVERPASS_URL = "https://overpass-api.de/api/interpreter"

USER_AGENT = (
    "BusinessHunter/1.0 "
    "(ferramenta de descoberta de empresas)"
)


MAPEAMENTO_CATEGORIAS = {
    "restaurante": ['["amenity"="restaurant"]'],
    "restaurantes": ['["amenity"="restaurant"]'],

    "café": ['["amenity"="cafe"]'],
    "cafés": ['["amenity"="cafe"]'],
    "cafe": ['["amenity"="cafe"]'],

    "bar": ['["amenity"="bar"]'],
    "bares": ['["amenity"="bar"]'],

    "lanchonete": ['["amenity"="fast_food"]'],
    "lanchonetes": ['["amenity"="fast_food"]'],

    "farmácia": ['["amenity"="pharmacy"]'],
    "farmácias": ['["amenity"="pharmacy"]'],

    "hotel": ['["tourism"="hotel"]'],
    "hotéis": ['["tourism"="hotel"]'],

    "academia": ['["leisure"="fitness_centre"]'],
    "academias": ['["leisure"="fitness_centre"]'],

    "clínica": ['["amenity"="clinic"]'],
    "clínicas": ['["amenity"="clinic"]'],

    "dentista": ['["amenity"="dentist"]'],
    "dentistas": ['["amenity"="dentist"]'],

    "clínica odontológica": ['["amenity"="dentist"]'],
    "clínicas odontológicas": ['["amenity"="dentist"]'],

    "salão de beleza": ['["shop"="beauty"]'],
    "salões de beleza": ['["shop"="beauty"]'],

    "barbearia": ['["shop"="hairdresser"]'],
    "barbearias": ['["shop"="hairdresser"]'],

    "supermercado": ['["shop"="supermarket"]'],
    "supermercados": ['["shop"="supermarket"]'],

    "padaria": ['["shop"="bakery"]'],
    "padarias": ['["shop"="bakery"]'],

    "pet shop": ['["shop"="pet"]'],
    "pet shops": ['["shop"="pet"]']
}


def extrair_termos_consulta(
    query: str
) -> tuple[str, str | None]:

    partes = re.split(
        r"\s+em\s+",
        query,
        maxsplit=1,
        flags=re.IGNORECASE
    )

    if len(partes) == 2:
        categoria = partes[0].strip()
        localizacao = partes[1].strip()

        return categoria, localizacao

    return query.strip(), None


def normalizar_localizacao(localizacao: str) -> str:
    """
    Remove informações estaduais adicionadas ao nome da cidade.

    Exemplo:
    "Cornélio Procópio PR"
    -> "Cornélio Procópio"

    "Cornélio Procópio Paraná"
    -> "Cornélio Procópio"
    """

    resultado = localizacao.strip()

    resultado = re.sub(
        r"\s*-\s*(PR|Paraná)\s*$",
        "",
        resultado,
        flags=re.IGNORECASE
    )

    resultado = re.sub(
        r"\s+(PR|Paraná)\s*$",
        "",
        resultado,
        flags=re.IGNORECASE
    )

    return resultado.strip()


def normalizar_categoria(categoria: str) -> list[str]:

    categoria_normalizada = (
        categoria
        .strip()
        .lower()
    )

    if categoria_normalizada in MAPEAMENTO_CATEGORIAS:
        return MAPEAMENTO_CATEGORIAS[
            categoria_normalizada
        ]

    return [
        f'["name"~"{re.escape(categoria)}", i]'
    ]


def construir_query_overpass(
    categoria: str,
    localizacao: str | None
) -> str:

    filtros = normalizar_categoria(
        categoria
    )

    if localizacao:

        localizacao = normalizar_localizacao(
            localizacao
        )

        consultas = []

        for filtro in filtros:

            consultas.append(
                f'nwr{filtro}(area.searchArea);'
            )

        consultas_elementos = "\n".join(
            consultas
        )

        return f"""
[out:json][timeout:30];

area["name"="{localizacao}"]["boundary"="administrative"]->.searchArea;

(
{consultas_elementos}
);

out center tags;
""".strip()

    consultas = []

    for filtro in filtros:

        consultas.append(
            f'nwr{filtro}(-34.0,-74.0,6.0,-28.0);'
        )

    consultas_elementos = "\n".join(
        consultas
    )

    return f"""
[out:json][timeout:30];

(
{consultas_elementos}
);

out center tags;
""".strip()


def obter_localizacao(
    elemento: dict
) -> tuple[float | None, float | None]:

    latitude = elemento.get("lat")
    longitude = elemento.get("lon")

    if latitude is not None and longitude is not None:
        return latitude, longitude

    center = elemento.get(
        "center",
        {}
    )

    return (
        center.get("lat"),
        center.get("lon")
    )


def montar_endereco(tags: dict) -> str:

    partes = []

    rua = tags.get("addr:street")
    numero = tags.get("addr:housenumber")
    bairro = tags.get("addr:suburb")
    cidade = tags.get("addr:city")
    estado = tags.get("addr:state")

    if rua:
        partes.append(rua)

    if numero:
        partes.append(numero)

    if bairro:
        partes.append(bairro)

    if cidade:
        partes.append(cidade)

    if estado:
        partes.append(estado)

    return ", ".join(partes)


def pesquisar_web(
    query: str,
    quantidade: int = 10
) -> dict:

    if not query.strip():
        raise ValueError(
            "A consulta de pesquisa não pode estar vazia."
        )

    quantidade = max(
        1,
        min(
            20,
            quantidade
        )
    )

    categoria, localizacao = extrair_termos_consulta(query)

    overpass_query = construir_query_overpass(
        categoria,
        localizacao
    )

    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/json"
    }

    try:
        response = requests.post(
            OVERPASS_URL,
            data={
                "data": overpass_query
            },
            headers=headers,
            timeout=60
        )

        response.raise_for_status()

    except requests.exceptions.Timeout:
        raise RuntimeError(
            "A pesquisa no OpenStreetMap/Overpass "
            "excedeu o tempo limite."
        )

    except requests.exceptions.RequestException as error:
        raise RuntimeError(
            f"Erro ao consultar o Overpass API: {error}\n"
            f"Resposta: {response.text}"
        )

    data = response.json()

    print("\nRESULTADO BRUTO DO OVERPASS:")
    print(
        json.dumps(
            data,
            ensure_ascii=False,
            indent=2
        )
    )

    resultados = []

    for elemento in data.get("elements", []):

        tags = elemento.get("tags", {})

        resultados.append({
            "nome": tags.get("name", ""),
            "endereco": montar_endereco(tags),
            "telefone": tags.get("phone", ""),
            "site": tags.get("website", "")
        })

    resultados = resultados[:quantidade]

    return {
        "consulta": query,
        "quantidade_resultados": len(resultados),
        "resultados": resultados
    }


pesquisar_web_tool = {
    "name": "pesquisar_web",
    "description": (
        "Pesquisa empresas e estabelecimentos utilizando "
        "dados públicos do OpenStreetMap através do Overpass API. "
        "Use essa ferramenta para descobrir empresas por "
        "segmento, cidade ou região. "
        "Os resultados retornados devem ser analisados antes "
        "de realizar novas pesquisas."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": (
                    "Consulta contendo o segmento e, quando "
                    "necessário, a cidade ou região. "
                    "Exemplo: "
                    "'clínicas odontológicas em Cornélio Procópio PR'."
                )
            },
            "quantidade": {
                "type": "integer",
                "description": (
                    "Quantidade máxima de resultados desejados. "
                    "Prefira valores entre 5 e 10."
                ),
                "minimum": 1,
                "maximum": 20,
                "default": 10
            }
        },
        "required": [
            "query"
        ]
    }
}


if __name__ == "__main__":

    resultado = pesquisar_web(
        "clínicas odontológicas em Cornélio Procópio PR",
        quantidade=5
    )

    print(
        f"\nConsulta: {resultado['consulta']}"
    )

    print(
        f"Resultados encontrados: "
        f"{resultado['quantidade_resultados']}\n"
    )

    for empresa in resultado["resultados"]:

        print(
            empresa
        )
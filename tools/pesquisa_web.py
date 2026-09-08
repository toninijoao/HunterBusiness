import re
import requests

from urllib.parse import quote


OVERPASS_URL = "https://overpass-api.de/api/interpreter"

USER_AGENT = (
    "BusinessHunter/1.0 "
    "(projeto de descoberta de empresas)"
)


def extrair_termos_consulta(query: str) -> tuple[str, str | None]:
    """
    Tenta extrair uma categoria e uma localização da consulta.

    Exemplos:
        "clínicas odontológicas em Cornélio Procópio PR"
        -> ("clínicas odontológicas", "Cornélio Procópio PR")

        "restaurantes em Londrina PR"
        -> ("restaurantes", "Londrina PR")

    Quando não consegue identificar uma localização,
    mantém a consulta inteira como categoria.
    """

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


def normalizar_categoria(categoria: str) -> list[str]:
    """
    Converte termos comuns de negócio para categorias/tags
    utilizadas pelo OpenStreetMap.

    O resultado é uma lista de filtros possíveis.
    """

    categoria_normalizada = categoria.lower().strip()

    categorias = []

    mapeamento = {
        "restaurante": [
            ('["amenity"="restaurant"]')
        ],
        "restaurantes": [
            ('["amenity"="restaurant"]')
        ],
        "café": [
            ('["amenity"="cafe"]')
        ],
        "cafés": [
            ('["amenity"="cafe"]')
        ],
        "cafe": [
            ('["amenity"="cafe"]')
        ],
        "lanchonete": [
            ('["amenity"="fast_food"]')
        ],
        "lanchonetes": [
            ('["amenity"="fast_food"]')
        ],
        "bar": [
            ('["amenity"="bar"]')
        ],
        "bares": [
            ('["amenity"="bar"]')
        ],
        "farmácia": [
            ('["amenity"="pharmacy"]')
        ],
        "farmácias": [
            ('["amenity"="pharmacy"]')
        ],
        "hotel": [
            ('["tourism"="hotel"]')
        ],
        "hotéis": [
            ('["tourism"="hotel"]')
        ],
        "academia": [
            ('["leisure"="fitness_centre"]')
        ],
        "academias": [
            ('["leisure"="fitness_centre"]')
        ],
        "clínica": [
            ('["amenity"="clinic"]')
        ],
        "clínicas": [
            ('["amenity"="clinic"]')
        ],
        "hospital": [
            ('["amenity"="hospital"]')
        ],
        "hospitais": [
            ('["amenity"="hospital"]')
        ],
        "dentista": [
            ('["amenity"="dentist"]')
        ],
        "dentistas": [
            ('["amenity"="dentist"]')
        ],
        "clínicas odontológicas": [
            ('["amenity"="dentist"]')
        ],
        "salão de beleza": [
            ('["shop"="beauty"]')
        ],
        "salões de beleza": [
            ('["shop"="beauty"]')
        ],
        "barbearia": [
            ('["shop"="hairdresser"]')
        ],
        "barbearias": [
            ('["shop"="hairdresser"]')
        ],
        "supermercado": [
            ('["shop"="supermarket"]')
        ],
        "supermercados": [
            ('["shop"="supermarket"]')
        ],
        "padaria": [
            ('["shop"="bakery"]')
        ],
        "padarias": [
            ('["shop"="bakery"]')
        ],
        "pet shop": [
            ('["shop"="pet"]')
        ],
        "pet shops": [
            ('["shop"="pet"]')
        ]
    }

    if categoria_normalizada in mapeamento:
        return mapeamento[categoria_normalizada]

    return [
        f'[~"name|description|brand|operator"~"{re.escape(categoria)}", i]'
    ]


def construir_query_overpass(
    categoria: str,
    localizacao: str | None,
    quantidade: int
) -> str:

    filtros = normalizar_categoria(categoria)

    if localizacao:
        area_nome = localizacao

        consulta_filtros = []

        for filtro in filtros:
            consulta_filtros.append(
                f'nwr{filtro}(area.searchArea);'
            )

        consulta_elementos = "\n".join(
            consulta_filtros
        )

        return f"""
[out:json][timeout:30];

area["name"="{area_nome}"]["boundary"="administrative"]->.searchArea;

(
{consulta_elementos}
);

out center tags;
""".strip()

    consulta_filtros = []

    for filtro in filtros:
        consulta_filtros.append(
            f'nwr{filtro}(-34.0,-74.0,6.0,-28.0);'
        )

    consulta_elementos = "\n".join(
        consulta_filtros
    )

    return f"""
[out:json][timeout:30];

(
{consulta_elementos}
);

out center tags;
""".strip()


def obter_localizacao(elemento: dict) -> tuple[float | None, float | None]:
    latitude = elemento.get("lat")
    longitude = elemento.get("lon")

    if latitude is not None and longitude is not None:
        return latitude, longitude

    center = elemento.get("center", {})

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

    categoria, localizacao = extrair_termos_consulta(
        query
    )

    overpass_query = construir_query_overpass(
        categoria=categoria,
        localizacao=localizacao,
        quantidade=quantidade
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

        try:
            detalhes = response.text
        except Exception:
            detalhes = ""

        raise RuntimeError(
            "Erro ao consultar o Overpass API: "
            f"{error}\n"
            f"Resposta: {detalhes}"
        )

    try:
        data = response.json()

    except ValueError:
        raise RuntimeError(
            "O Overpass retornou uma resposta que "
            "não pôde ser interpretada como JSON."
        )

    resultados = []

    elementos = data.get(
        "elements",
        []
    )

    elementos_vistos = set()

    for elemento in elementos:

        tags = elemento.get(
            "tags",
            {}
        )

        nome = (
            tags.get("name")
            or tags.get("brand")
            or tags.get("operator")
        )

        if not nome:
            continue

        elemento_id = (
            elemento.get("type"),
            elemento.get("id")
        )

        if elemento_id in elementos_vistos:
            continue

        elementos_vistos.add(
            elemento_id
        )

        latitude, longitude = obter_localizacao(
            elemento
        )

        endereco = montar_endereco(
            tags
        )

        website = (
            tags.get("website")
            or tags.get("contact:website")
            or ""
        )

        telefone = (
            tags.get("phone")
            or tags.get("contact:phone")
            or ""
        )

        instagram = (
            tags.get("contact:instagram")
            or ""
        )

        facebook = (
            tags.get("contact:facebook")
            or ""
        )

        resultado = {
            "place_id": (
                f"osm:{elemento.get('type')}:"
                f"{elemento.get('id')}"
            ),
            "nome": nome,
            "endereco": endereco,
            "telefone": telefone,
            "google_maps": "",
            "site": website,
            "tipo_principal": (
                tags.get("amenity")
                or tags.get("shop")
                or tags.get("tourism")
                or tags.get("leisure")
                or ""
            ),
            "tipos": [],
            "cidade": (
                tags.get("addr:city")
                or localizacao
                or ""
            ),
            "estado": (
                tags.get("addr:state")
                or ""
            ),
            "latitude": latitude,
            "longitude": longitude,
            "fonte": "OpenStreetMap"
        }

        resultados.append(
            resultado
        )

        if len(resultados) >= quantidade:
            break

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
        "Analise os resultados retornados antes de realizar "
        "novas pesquisas."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": (
                    "Consulta de pesquisa contendo o segmento "
                    "e, quando necessário, a cidade ou região. "
                    "Exemplo: "
                    "'clínicas odontológicas em Cornélio Procópio PR'."
                )
            },
            "quantidade": {
                "type": "integer",
                "description": (
                    "Quantidade máxima de resultados desejados. "
                    "Prefira valores entre 5 e 10 para gerar "
                    "várias candidatas."
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
        print(empresa)
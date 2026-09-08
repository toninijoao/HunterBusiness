import requests

from urllib.parse import urlencode


NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"

USER_AGENT = (
    "BusinessHunter/1.0 "
    "(ferramenta de geocodificação)"
)


def mapear_endereco(
    endereco: str,
    cidade: str | None = None,
    estado: str | None = None
) -> dict:

    if not endereco.strip():
        raise ValueError(
            "O endereço não pode estar vazio."
        )

    partes = [endereco]

    if cidade:
        partes.append(cidade)

    if estado:
        partes.append(estado)

    partes.append("Brasil")

    endereco_completo = ", ".join(partes)

    params = {
        "q": endereco_completo,
        "format": "jsonv2",
        "addressdetails": 1,
        "limit": 5,
        "countrycodes": "br",
        "accept-language": "pt-BR"
    }

    headers = {
        "User-Agent": USER_AGENT
    }

    try:
        response = requests.get(
            NOMINATIM_URL,
            params=params,
            headers=headers,
            timeout=30
        )

        response.raise_for_status()

    except requests.exceptions.Timeout:
        raise RuntimeError(
            "A consulta de localização excedeu o tempo limite."
        )

    except requests.exceptions.RequestException as error:
        raise RuntimeError(
            f"Erro ao consultar o Nominatim: {error}"
        )

    try:
        data = response.json()

    except ValueError:
        raise RuntimeError(
            "O Nominatim retornou uma resposta inválida."
        )

    if not data:
        return {
            "encontrado": False,
            "status": "NOT_FOUND",
            "endereco_original": endereco_completo,
            "resultados": []
        }

    resultados = []

    for resultado in data:

        address = resultado.get(
            "address",
            {}
        )

        resultados.append(
            {
                "endereco_formatado": resultado.get(
                    "display_name"
                ),
                "latitude": (
                    float(resultado["lat"])
                    if resultado.get("lat")
                    else None
                ),
                "longitude": (
                    float(resultado["lon"])
                    if resultado.get("lon")
                    else None
                ),
                "tipo": resultado.get(
                    "type"
                ),
                "place_id": resultado.get(
                    "osm_id"
                ),
                "osm_type": resultado.get(
                    "osm_type"
                ),
                "cidade": (
                    address.get("city")
                    or address.get("town")
                    or address.get("village")
                    or ""
                ),
                "estado": address.get(
                    "state",
                    ""
                ),
                "pais": address.get(
                    "country",
                    ""
                )
            }
        )

    return {
        "encontrado": len(resultados) > 0,
        "status": "OK",
        "endereco_original": endereco_completo,
        "resultados": resultados
    }


mapear_endereco_tool = {
    "name": "mapear_endereco",
    "description": (
        "Localiza geograficamente um endereço utilizando dados "
        "públicos do OpenStreetMap. Retorna endereço formatado, "
        "latitude, longitude, cidade, estado e identificadores "
        "do OpenStreetMap. Use para confirmar ou complementar "
        "informações geográficas de uma empresa."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "endereco": {
                "type": "string",
                "description": "Endereço da empresa."
            },
            "cidade": {
                "type": "string",
                "description": "Cidade da empresa, quando disponível."
            },
            "estado": {
                "type": "string",
                "description": "Estado da empresa, quando disponível."
            }
        },
        "required": [
            "endereco"
        ]
    }
}


if __name__ == "__main__":

    resultado = mapear_endereco(
        endereco="Rua Exemplo, 100",
        cidade="Cornélio Procópio",
        estado="PR"
    )

    print(resultado)
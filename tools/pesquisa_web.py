import os
import requests
from dotenv import load_dotenv

load_dotenv()
google_maps_api_key = os.getenv("GOOGLE_MAPS_API_KEY")
url = "https://places.googleapis.com/v1/places:searchText"

def pesquisar_web(
        query: str,
        quantidade: int = 10
) -> dict:

    if not google_maps_api_key:
        raise ValueError(
            "google_maps_api_key não encontrada no arquivo .env"
        )

    if not query.strip():
        raise ValueError(
            "A consulta de pesquisa não pode estar vazia."
    )

    quantidade = max(1, min(20, quantidade))

    headers = {
        "Content-Type": "application/json",
        "X-Goog-api-key": google_maps_api_key,
        "X-Goog-FieldMask": (
            "places.id,"
            "places.displayName,"
            "places.formattedAddress,"
            "places.nationalPhoneNumber,"
            "places.googleMapsUri,"
            "places.websiteUri,"
            "places.primaryType,"
            "places.types"
        )
    }

    payload = {
        "textQuery": query,
        "pageSize": quantidade,
        "languageCode": "pt-BR",
        "regionCode": "BR"
    }

    try:
        response = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=15
        )

        response.raise_for_status()

    except requests.exceptions.Timeout:
        raise RuntimeError(
            "A pesquisa no Google Places excedeu o tempo limite."
        )

    except requests.exceptions.RequestException as error:
        raise RuntimeError(
            f"Erro ao consultar o Google Places: {error}"
        )

    data = response.json()

    resultados = []

    for place in data.get("places", []):
        display_name = place.get("displayName", {})

        resultados.append(
            {
                "place_id": place.get("id"),
                "nome": display_name.get("text"),
                "endereco": place.get("formattedAddress"),
                "telefone": place.get("nationalPhoneNumber"),
                "google_maps": place.get("googleMapsUri"),
                "site": place.get("websiteUri"),
                "tipo_principal": place.get("primaryType"),
                "tipos": place.get("types", [])
            }
        )

    return {
        "consulta": query,
        "quantidade_resultados": len(resultados),
        "resultados": resultados
    }

pesquisar_web_tool = {
    "name": "pesquisar_web",
    "description": (
        "Pesquisa empresas no Google Places com base em uma consulta. "
        "Use essa ferramenta para descobrir empresas por segmento. "
        "Cidade ou região e obter informações públicas básicas sobre elas. "
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": (
                    "Consulta de pesquisa. "
                    "Exemplo: 'clínicas odontológicas em Cornélio Procópio PR'."
                )
            },
            "quantidade": {
                "type": "integer",
                "description": (
                    "Quantidade máxima de resultados desejados."
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

    for empresa in resultado["resultados"]:
        print(empresa)
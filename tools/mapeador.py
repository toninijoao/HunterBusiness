import os 
import requests
from dotenv import load_dotenv

load_dotenv()
google_maps_api_key = os.getenv("GOOGLE_MAPS_API_KEY")
url = "https://maps.googleapis.com/maps/api/geocode/json"

def mapear_endereco(
        endereco: str,
        cidade: str | None = None,
        estado: str | None = None
) -> dict:

    if not google_maps_api_key:
        raise ValueError(
            "GOOGLE_MAPS_API_KEY não encontrada no arquivo .env"
        )

    if not endereco.strip():
        raise ValueError(
            "O endereço não pode estar vazio"
        )

    partes=[endereco]

    if cidade:
        partes.append(cidade)

    if estado:
        partes.append(estado)

    partes.append("Brasil")

    endereco_completo = ", ".join(partes)

    params = {
        "address": endereco_completo,
        "key": google_maps_api_key,
        "language": "pt-BR",
        "region": "br"
    }

    try:
        response = requests.get(
            url,
            params=params,
            timeout=15
        )

        response.raise_for_status()

    except requests.exceptions.Timeout:
        raise RuntimeError(
            "A consulta de localização excedeu o tempo limite."
        )

    except requests.exceptions.RequestException as error:
        raise RuntimeError(
            f"Erro ao consultar o Google Geocoding: {error}"
        )

    data = response.json()

    if data.get("status") != "OK":
        return {
            "encontrado": False,
            "status": data.get("status"),
            "endereco_original": endereco_completo,
            "resultados": []
        }

    resultados = []

    for resultado in data.get("results", []):
        geometry = resultado.get("geometry", {})
        location = resultado.get("location", {})

        resultados.append(
            {
                "endereco_formatado": resultado.get(
                    "formatted_address"
                ),
                "latitude": location.get("lat"),
                "longitude": location.get("lng"),
                "tipo": geometry.get("location_type"),
                "place_id": resultado.get("place_id")
            }
        )

    return {
        "encontrado": len(resultados) > 0,
        "status": data.get("status"),
        "endereco_original": endereco_completo,
        "resultados": resultados
    }

mapear_endereco_tool = {
    "name": "mapear_endereco",
    "description": (
        "Localiza geograficamente um endereço e retorna o endereço formatado, latitude, longitude e identificadores de localização."
        "Use para confirmar ou complementar informações geográficas de uma empresa."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "endereco": {
                "type": "string",
                "description": "Endereço da empresa."
            },
            "cidade": {
                "type": ["string", "null"],
                "description": "Cidade da empresa."
            },
            "estado": {
                "type": ["string", "null"],
                "description": "Estado da empresa."
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
import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")

if not supabase_url:
    raise ValueError("SUPABASE_URL não encontrada no arquivo .env")

if not supabase_key:
    raise ValueError("SUPABASE_KEY não encontrada no arquivo .env")

supabase: Client = create_client(
    supabase_url,
    supabase_key
)

def buscar_empresa(nome: str, cidade: str | None = None, telefone: str | None = None) -> dict:
    query = (
        supabase
        .table("companies")
        .select("*")
        .ilike("name", nome)
    )

    if cidade:
        query = query.ilike("city", cidade)

    if telefone:
        query = query.eq("phone", telefone)

    response = query.execute()
    empresas = response.data or []

    return {
        "encontrada": len(empresas) > 0,
        "quantidade": len(empresas),
        "empresas": empresas
    }

def salvar_empresa(empresa: dict) -> dict:
    dados = {
        "name": empresa.get("nome"),
        "category": empresa.get("segmento"),
        "city": empresa.get("cidade"),
        "state": empresa.get("estado"),
        "country": empresa.get("pais", "Brasil"),
        "address": empresa.get("endereco"),
        "phone": empresa.get("telefone"),
        "instagram": empresa.get("instagram"),
        "facebook": empresa.get("facebook"),
        "google_maps": empresa.get("google_maps"),
        "website": empresa.get("site"),
        "website_status": empresa.get("website_status"),
        "website_confidence": empresa.get("website_confidence")
    }

    response = (
        supabase
        .table("companies")
        .insert(dados)
        .execute()
    )

    return {
        "sucesso": True,
        "empresa": response.data[0] if response.data else None
    }

buscar_empresa_tool = {
    "name": "buscar_empresa",
    "description": (
        "Consulta o banco de dados para verificar se uma empresa já foi registrada. Use antes de salvar uma nova empresa para evitar duplicatas."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "nome": {
                "type": "string",
                "description": "Nome da empresa."
            },
            "cidade": {
                "type": ["string", "null"],
                "description": "Cidade da empresa."
            },
            "telefone": {
                "type": ["string", "null"],
                "description": "Telefone da empresa, caso disponível."
            }
        },
        "required": [
            "nome"
        ]
    }
}

salvar_empresa_tool = {
    "name": "salvar_empresa",
    "description": (
        "Salva uma empresa validada no banco de dados. Use somente depois de confirmar que a empresa é válida e não está duplicada."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "empresa": {
                "type": "object",
                "description": ("Dados estruturados da empresa validada.")
            }
        },
        "required": [
            "empresa"
        ]
    }
}

if __name__ == "__main__":
    resultado = buscar_empresa(
        nome="Empresa Exemplo",
        cidade="Cornélio Procópio"
    )

    print(resultado)
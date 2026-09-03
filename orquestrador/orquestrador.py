import json
from pathlib import Path
import yaml
from agentes.agente_hunter import executar_hunter
from agentes.agente_filtro import executar_filtro
from agentes.agente_arquiteto import executar_arquiteto
from agentes.agente_planilha import executar_planilha

base_dir = Path(__file__).resolve().parent.parent
config_path = base_dir / "config" / "config.yaml"

def carregar_config() -> dict:
    if not config_path.exists():
        raise FileNotFoundError(f"Arquivo de configuração não encontrado: {config_path}")

    with config_path.open("r", encoding="utf-8") as arquivo:
        return yaml.safe_load(arquivo)

def criar_tarefa(config: dict) -> str:
    quantidade = config.get("quantidade_empresas", 20)
    localizacoes = config.get("localizacoes_prioritarias", [])
    segmentos = config.get("segmentos", [])

    if not localizacoes:
        raise ValueError(
            "Nenhuma localização foi configurada."
        )

    if not segmentos:
        raise ValueError(
            "Nenhum segmento foi configurado."
        )

    locais_formatados = "\n".join(
        f"{i + 1}. {local}"
        for i, local in enumerate(localizacoes)
    )

    segmentos_formatados = "\n".join(
        f"- {segmento}"
        for segmento in segmentos
    )

    return f"""
    Encontre {quantidade} empresas de pequeno ou médio porte no Brasil.

    Prioridade geográfica:
    {locais_formatados}

    Segmentos permitidos:
    {segmentos_formatados}

    Critérios obrigatórios:

    - A empresa deve estar ativa.
    - A empresa deve pertencer a um dos segmentos configurados.
    - A empresa deve ser de pequeno ou médio porte, quando isso puder ser estimado.
    - A empresa não deve possuir um site oficial funcional.
    - Não considere Instagram, Facebook, Google Maps, diretórios ou marketplaces como site oficial.
    - Não inclua empresas já existentes no banco de dados.
    - Valide cuidadosamente a ausência de um site antes de considerar a empresa válida.
    - Não invente informações.
    - Priorize empresas encontradas em Cornélio Procópio, e, depois, nas demais regiões prioritárias.

    Retorne somente empresas que atendam aos critérios.
"""

def executar_pipeline(tarefa: str) -> dict:
    empresas = executar_hunter(tarefa)

    if not isinstance(empresas, dict):
        raise ValueError(
            "O hunter não retornou um objeto válido."
        )

    lista_empresas = empresas.get("empresas", [])

    if not isinstance(lista_empresas, list):
        raise ValueError(
            "O campo 'empresas' retornado pelo Hunter deve ser uma lista."
        )

    resultados = []

    for empresa in lista_empresas:
        try:
            perfil = executar_filtro(empresa)
            solucao = executar_arquiteto(perfil)
            dados_planilha = executar_planilha(empresa, perfil, solucao)
            resultados.append(
                {
                    "empresa": empresa,
                    "perfil": perfil,
                    "solucao": solucao,
                    "planilha": dados_planilha
                }
            )

        except Exception as error:
            resultados.append(
                {
                    "empresa": empresa,
                    "erro": str(error)
                }
            )

    return {
        "quantidade_encontrada": len(lista_empresas),
        "quantidade_processada": len(resultados),
        "resultados": resultados
    }

if __name__ == "__main__":
    config = carregar_config()
    tarefa = criar_tarefa(config)
    resultado = executar_pipeline(tarefa)

    print(json.dumps(resultado, ensure_ascii=False, indent=4))
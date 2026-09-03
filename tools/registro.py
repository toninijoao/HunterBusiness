from tools.pesquisa_web import (
    pesquisar_web,
    pesquisar_web_tool
)

from tools.checkagem_site import(
    verificar_site,
    verificar_site_tool
)

from tools.mapeador import (
    mapear_endereco,
    mapear_endereco_tool
)

from tools.database import (
    buscar_empresa,
    buscar_empresa_tool,
    salvar_empresa,
    salvar_empresa_tool
)

tools = [
    pesquisar_web_tool,
    verificar_site_tool,
    mapear_endereco_tool,
    buscar_empresa_tool,
    salvar_empresa_tool
]

tool_functions = {
    "pesquisar_web": pesquisar_web,
    "verificar_site": verificar_site,
    "mapear_endereco": mapear_endereco,
    "buscar_empresa": buscar_empresa,
    "salvar_empresa": salvar_empresa
}
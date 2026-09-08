from tools.pesquisa_web import pesquisar_web
from tools.checkagem_site import verificar_site
from tools.mapeador import mapear_endereco
from tools.database import buscar_empresa, salvar_empresa


tools = [
    pesquisar_web,
    verificar_site,
    mapear_endereco,
    buscar_empresa,
    salvar_empresa
]


tool_functions = {
    "pesquisar_web": pesquisar_web,
    "verificar_site": verificar_site,
    "mapear_endereco": mapear_endereco,
    "buscar_empresa": buscar_empresa,
    "salvar_empresa": salvar_empresa
}
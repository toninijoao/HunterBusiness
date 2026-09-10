const API_BASE_URL = "http://127.0.0.1:8000";

interface Empresa {
  name: string;
  city: string;
  state: string;
  country: string;
  address: string;
  phone: string;
  instagram: string;
  facebook: string;
  google_maps: string;
  website: string;
  website_status: string;
  website_confidence: number;
  sources?: string[];
}

interface ResultadoItem {
  empresa: Empresa;
  erro?: string;
}

interface ResultadoPipeline {
  quantidade_encontrada: number;
  quantidade_processada: number;
  resultados: ResultadoItem[];
}

const STATUS_LEGIVEL: Record<string, string> = {
  WEBSITE_NOT_FOUND: "Sem site",
  WEBSITE_FOUND: "Tem site",
  WEBSITE_UNCERTAIN: "Incerto"
};

const botao = document.querySelector<HTMLButtonElement>("#botao-iniciar");
const elementoStatus = document.querySelector<HTMLParagraphElement>("#status");
const corpoTabela = document.querySelector<HTMLTableSectionElement>("#corpo-tabela");

if (!botao || !elementoStatus || !corpoTabela) {
  throw new Error("Elementos da página não encontrados.");
}

function limparTabela(): void {
  corpoTabela!.innerHTML = "";
}

function criarCelula(texto: string): HTMLTableCellElement {
  const celula = document.createElement("td");
  celula.textContent = texto;
  return celula;
}

function renderizarLinha(item: ResultadoItem): void {
  const linha = document.createElement("tr");

  if (item.erro) {
    linha.appendChild(criarCelula(item.empresa?.name ?? ""));
    const celulaErro = document.createElement("td");
    celulaErro.colSpan = 5;
    celulaErro.textContent = `Erro ao processar: ${item.erro}`;
    linha.appendChild(celulaErro);
    corpoTabela!.appendChild(linha);
    return;
  }

  const empresa = item.empresa;

  linha.appendChild(criarCelula(empresa.name || ""));
  linha.appendChild(
    criarCelula(
      [empresa.city, empresa.state].filter(Boolean).join(" / ")
    )
  );
  linha.appendChild(criarCelula(empresa.phone || ""));
  linha.appendChild(criarCelula(empresa.address || ""));

  const celulaSite = document.createElement("td");
  if (empresa.google_maps) {
    const link = document.createElement("a");
    link.href = empresa.google_maps;
    link.target = "_blank";
    link.rel = "noopener noreferrer";
    link.textContent = "Google Maps";
    celulaSite.appendChild(link);
  }
  linha.appendChild(celulaSite);

  linha.appendChild(
    criarCelula(
      STATUS_LEGIVEL[empresa.website_status] ?? empresa.website_status ?? ""
    )
  );

  corpoTabela!.appendChild(linha);
}

async function iniciarBusca(): Promise<void> {
  botao!.disabled = true;
  elementoStatus!.textContent = "Buscando... isso pode levar alguns minutos.";
  limparTabela();

  try {
    const resposta = await fetch(`${API_BASE_URL}/executar`, {
      method: "POST"
    });

    if (!resposta.ok) {
      const corpo = await resposta.text();
      throw new Error(`${resposta.status} - ${corpo}`);
    }

    const resultado: ResultadoPipeline = await resposta.json();

    if (resultado.resultados.length === 0) {
      elementoStatus!.textContent = "Nenhuma empresa encontrada.";
      return;
    }

    resultado.resultados.forEach(renderizarLinha);

    elementoStatus!.textContent =
      `${resultado.quantidade_encontrada} empresa(s) encontrada(s), ` +
      `${resultado.quantidade_processada} processada(s).`;

  } catch (erro) {
    elementoStatus!.textContent = `Falha ao executar a busca: ${(erro as Error).message}`;

  } finally {
    botao!.disabled = false;
  }
}

botao.addEventListener("click", () => {
  void iniciarBusca();
});

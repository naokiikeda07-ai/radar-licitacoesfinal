from datetime import datetime, timedelta
import json
import time
import requests

DATA_FIM = datetime.now().strftime("%Y%m%d")
DATA_INICIO = (datetime.now() - timedelta(days=3)).strftime("%Y%m%d")

URL_PNCP = "https://pncp.gov.br/api/consulta/v1/contratacoes/publicacao"
TODAS_MODALIDADES = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13]

PALAVRAS_ENGENHARIA = [
    "obra",
    "obras",
    "engenharia",
    "pavimentação",
    "pavimentacao",
    "recapeamento",
    "asfáltica",
    "asfaltica",
    "cbuq",
    "tapa-buraco",
    "drenagem",
    "macrodrenagem",
    "galeria",
    "saneamento",
    "esgoto",
    "adutora",
    "abastecimento de água",
    "estação elevatória",
    "edificação",
    "edificacao",
    "construção",
    "construcao",
    "reforma",
    "ampliação",
    "ampliacao",
    "manutenção predial",
    "manutencao predial",
    "terraplenagem",
    "contenção",
    "contencao",
    "muro de arrimo",
    "talude",
    "ponte",
    "viaduto",
    "passarela",
    "obra de arte especial",
    "infraestrutura",
    "urbanização",
    "urbanizacao",
    "praça",
    "quadra",
    "escola",
    "creche",
    "ubs",
    "hospital",
    "unidade básica",
    "impermeabilização",
    "cobertura",
    "telhado",
    "estrutura metálica",
    "concreto armado",
    "fundação",
    "sondagem",
    "topografia",
    "projeto executivo",
    "projeto básico",
    "fiscalização de obra",
    "gerenciamento de obra",
    "laudo técnico",
    "elétrica",
    "hidrossanitária",
    "subestação",
    "iluminação pública",
    "sinalização viária",
    "ciclovia",
    "calçada",
    "acessibilidade",
]

PALAVRAS_EXCLUIR = [
    "aquisição de medicamentos",
    "aquisição de gêneros alimentícios",
    "aquisição de veículos",
    "aquisição de material de expediente",
    "aquisição de mobiliário",
    "aquisição de computadores",
    "locação de veículos",
]

headers = {"User-Agent": "Mozilla/5.0 (RadarLicitacoesEngenharia/2.0)"}
licitacoes_dict = {}

for mod in TODAS_MODALIDADES:
  pagina = 1
  while True:
    params = {
        "dataInicial": DATA_INICIO,
        "dataFinal": DATA_FIM,
        "codigoModalidadeContratacao": mod,
        "pagina": pagina,
        "tamanhoPagina": 100,
    }
    try:
      resp = requests.get(URL_PNCP, params=params, headers=headers, timeout=25)
      if resp.status_code != 200:
        break
      corpo = resp.json()
      dados = corpo.get("data", [])
      total_paginas = corpo.get("totalPaginas", 1)
      if not dados:
        break

      for item in dados:
        objeto = item.get("objetoCompra", "")
        obj_lower = objeto.lower()
        if any(p in obj_lower for p in PALAVRAS_ENGENHARIA) and not any(
            p in obj_lower for p in PALAVRAS_EXCLUIR
        ):
          id_pncp = item.get("numeroControlePNCP")
          cnpj = item.get("orgaoEntidade", {}).get("cnpj")
          ano = item.get("anoCompra")
          seq = item.get("sequencialCompra")
          licitacoes_dict[id_pncp] = {
              "id": id_pncp,
              "fonte": "PNCP",
              "modalidade": item.get("modalidadeNome", ""),
              "orgao": item.get("orgaoEntidade", {}).get("razaoSocial", ""),
              "uf": item.get("unidadeOrgao", {}).get("ufSigla", "BR"),
              "municipio": item.get("unidadeOrgao", {}).get("municipioNome", ""),
              "objeto": objeto,
              "valor_estimado": item.get("valorTotalEstimado") or 0,
              "data_publicacao": item.get("dataPublicacaoPncp", ""),
              "data_abertura": item.get("dataAberturaProposta", ""),
              "status": "Nova",
              "link": (
                  f"https://pncp.gov.br/app/editais/{cnpj}/{ano}/{seq}"
                  if cnpj
                  else "https://pncp.gov.br"
              ),
          }

      if pagina >= total_paginas:
        break
      pagina += 1
      time.sleep(0.2)
    except Exception:
      break

try:
  url_comprasgov = "https://dadosabertos.compras.gov.br/modulo-contratacoes/1_consultarContratacoes_PNCP_14133"
  params_cg = {
      "dataPublicacaoPncpInicial": (
          datetime.now() - timedelta(days=3)
      ).strftime("%Y-%m-%d"),
      "dataPublicacaoPncpFinal": datetime.now().strftime("%Y-%m-%d"),
      "pagina": 1,
      "tamanhoPagina": 100,
  }
  resp_cg = requests.get(
      url_comprasgov, params=params_cg, headers=headers, timeout=20
  )
  if resp_cg.status_code == 200:
    for item in resp_cg.json().get("resultado", []):
      objeto = item.get("objetoCompra", "")
      obj_lower = objeto.lower()
      if any(p in obj_lower for p in PALAVRAS_ENGENHARIA) and not any(
          p in obj_lower for p in PALAVRAS_EXCLUIR
      ):
        id_cg = item.get("numeroControlePNCP") or f"CG-{item.get('idCompra')}"
        if id_cg not in licitacoes_dict:
          licitacoes_dict[id_cg] = {
              "id": id_cg,
              "fonte": "Compras.gov.br",
              "modalidade": item.get("modalidadeNome", ""),
              "orgao": item.get("orgaoEntidadeRazaoSocial", ""),
              "uf": item.get("unidadeOrgaoUfSigla", "BR"),
              "municipio": item.get("unidadeOrgaoMunicipioNome", ""),
              "objeto": objeto,
              "valor_estimado": item.get("valorTotalEstimado") or 0,
              "data_publicacao": item.get("dataPublicacaoPncp", ""),
              "data_abertura": item.get("dataAberturaProposta", ""),
              "status": "Nova",
              "link": "https://cnetmobile.estaleiro.serpro.gov.br/comprasnet-web/public/compras",
          }
except Exception:
  pass

resultado_final = sorted(
    licitacoes_dict.values(),
    key=lambda x: x.get("data_publicacao") or "",
    reverse=True,
)
with open("licitacoes_hoje.json", "w", encoding="utf-8") as f:
  json.dump(resultado_final, f, ensure_ascii=False, indent=2)

print(f"Concluído: {len(resultado_final)} licitações salvas.")
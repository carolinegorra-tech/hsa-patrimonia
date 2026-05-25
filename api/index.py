"""
HSA Patrimon.IA — FastAPI app for Vercel Python runtime.

Vercel routes any path starting with /api/* to this file (via vercel.json).
Everything else (the frontend) is served as a static asset by Vercel's CDN
from the /public folder — we do NOT mount static here.

Auth model (mudou em 2026-05):
  • Senha do escritório: HARDCODED como "humberto". Bater senha de uma vez
    no /login destrava o app no navegador do usuário.
  • API key do Anthropic: cada usuário fornece a SUA própria chave após o
    login. A chave nunca é guardada no servidor — vai em cada requisição
    no header X-Anthropic-Api-Key.

Env vars (set in the Vercel dashboard):
  CORS_ORIGINS        optional, comma-separated; default "*"
  ANTHROPIC_MODEL     optional override
"""
from __future__ import annotations

import base64
import json
import logging
import os
import re
import tempfile
import uuid
from pathlib import Path
from typing import Any

import httpx
from fastapi import Depends, FastAPI, File, Header, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

# deck_builder and excel_builder live in api/lib/ — make Python find them
import sys, os as _os_path
sys.path.insert(0, _os_path.path.join(_os_path.path.dirname(__file__), "lib"))
import deck_builder
import excel_builder

# Senha hardcoded do escritório. Não é segredo criptográfico — é só um gate
# pra evitar que alguém com a URL random encontre o app. Pode mudar pra
# qualquer string aqui.
HSA_PASSWORD      = "humberto"
CORS_ORIGINS      = os.environ.get("CORS_ORIGINS", "*").split(",")
ANTHROPIC_MODEL   = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")
ANTHROPIC_URL     = "https://api.anthropic.com/v1/messages"

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("hsa")

app = FastAPI(title="HSA Patrimon.IA", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


def auth(x_hsa_password: str | None = Header(default=None)) -> None:
    """Gate cada endpoint sensível com a senha do escritório."""
    if x_hsa_password != HSA_PASSWORD:
        raise HTTPException(status_code=401, detail="invalid or missing password")


EXTRACT_PROMPT = """Extraia todos os bens, direitos e informações familiares deste(s) documento(s) e retorne APENAS JSON válido (sem markdown, sem ```):
{"client":"NOME COMPLETO","cpf":"000.000.000-00","year":2024,"spouse":{"name":"","cpf":"","marriage_regime":"","marriage_date":"","certificate_registry":""},"dependents":[{"name":"","cpf":"","birth_date":"","relationship":""}],"groups":[{"name":"categoria","jurisdiction":"Brasil ou Offshore","items":[{"id":1,"desc":"descrição do ativo","loc":"cidade/país","subcategory":"","subsubcategory":"","confidence":"high|low","dirpf":valor_numerico_ou_null,"dcbe":valor_numerico_ou_null,"comments":""}]}],"debts":[{"id":1,"desc":"descrição da dívida","subcategory":"","subsubcategory":"","confidence":"high|low","value":valor_numerico}]}

REGRAS CRÍTICAS:
1. EXTRAIA ITEM POR ITEM — não use o total do grupo. Crie UM item para CADA bem listado nos PDFs, com sua descrição completa e valor individual em 31/12 do ano da declaração.
2. Se a soma dos itens individuais não bater exatamente com o "Total Grupo X" do DIRPF, mantenha os valores individuais como foram declarados (a diferença pode ser ajustes do meio do ano).

3. JURISDIÇÃO — Defina pela LOCALIZAÇÃO REAL do ativo (campo "País" da DIRPF), NÃO pelo documento de origem:
   - jurisdiction = "Brasil"   → ativo no Brasil (campo País = "Brasil" / código 105)
   - jurisdiction = "Offshore" → ativo no exterior (qualquer outro país)

   ⚠ ATENÇÃO MÁXIMA: O DIRPF declara o patrimônio GLOBAL em BRL — INCLUI ativos no exterior. NÃO assuma que tudo que vem do DIRPF é "Brasil". Olhe o campo "País" de CADA item antes de classificar.

   Códigos DIRPF que tipicamente identificam ativos NO EXTERIOR (sempre confirme olhando o campo "País" do item):
   - Grupo 03 Participações: 31 (Ações no exterior), 39 (Outras participações exterior), 73 (Trust — Lei 14.754/23), 74 (Outras part. empresa exterior), 76 (Entidade controlada no exterior — Lei 14.754)
   - Grupo 04 Aplicações: 45 (Ativos virtuais / cripto), 47, 79 (Aplicações no exterior)
   - Grupo 06 Contas: qualquer código com País ≠ Brasil (conta em banco estrangeiro)
   - Grupo 01 Imóveis: imóvel com País ≠ Brasil
   - Todos os itens do DCBE → Offshore por definição

4. MERGE DIRPF + DCBE — Quando o MESMO ativo offshore aparece nos DOIS documentos (mesma entidade/empresa/banco, mesmo país), UNA em UM ÚNICO item:
   - jurisdiction: "Offshore"
   - dirpf: valor em R$ (vindo da DIRPF)
   - dcbe: valor em USD (vindo da DCBE)
   - desc: nome da entidade (use a versão mais completa entre os dois documentos)
   - loc: país de localização

   Exemplo: "DOE FAMILY HOLDINGS LTD." aparece na DIRPF código 74 com R$ 17.000.000 E na DCBE Ficha A com US$ 3.420.000 → cria UM único item: {desc:"DOE FAMILY HOLDINGS LTD.", loc:"Ilhas Cayman", jurisdiction:"Offshore", subcategory:"Participação em empresa no exterior (LLC, offshore, BVI, Cayman)", dirpf:17000000, dcbe:3420000, ...}

   NUNCA crie dois itens separados (um só com dirpf, outro só com dcbe) se eles representam a MESMA entidade. Faça match por nome de entidade (banco, empresa, fundo, trust, conta). Variações como "Citibank Private Bank" vs "Citibank International" ou "Doe Holdings Ltd." vs "Doe Holdings Limited" DEVEM ser merged. Se não conseguir fazer o match com certeza razoável, mantenha separado.

5. dirpf = valor em R$ da DIRPF; dcbe = valor em USD da DCBE (item pode ter apenas um dos dois ou ambos)
6. Inclua dívidas da Ficha 8 no array "debts" (uma entrada por dívida)
7. Inclua cônjuge da Ficha 2 em "spouse"; dependentes da Ficha 3
8. JSON 100% completo e fechado. Valores SEMPRE numéricos com centavos exatos.

CLASSIFICAÇÃO OBRIGATÓRIA (3 níveis) — Para cada item, ESCOLHA OBRIGATORIAMENTE a melhor opção (nunca deixe em branco):
- name: grupo (nível 1)
- subcategory: subcategoria do grupo (nível 2)
- subsubcategory: instrumento/sub-item (nível 3) — só preenche se a subcategoria tiver sub-itens listados abaixo
- confidence: "high" se a descrição deixa CLARO a subcategoria/instrumento; "low" se você teve que CHUTAR a opção mais provável.

GRUPOS válidos para "name":
"Bens Imóveis" | "Bens Móveis" | "Participações Societárias" | "Aplicações e Investimentos" | "Previdência Privada" | "Créditos e Direitos" | "Contas Bancárias e Saldos" | "Criptoativos" | "Remuneração Variável em Equity"

SUBCATEGORIAS e SUB-ITENS por grupo:

• Bens Imóveis → subcategory ∈ {"Residenciais","Comerciais e Industriais","Rurais","Outros"}; subsubcategory = ""
  Dica: apartamento/casa = Residenciais; loja/sala/galpão = Comerciais; fazenda/sítio = Rurais.

• Bens Móveis → subcategory ∈ {"Veículos","Aviação e Náutica","Arte, Joias e Coleções","Outros","NFT / Ativo Digital Não Fungível"}; subsubcategory = ""
  Dica: carro/moto = Veículos; barco/iate/avião = Aviação e Náutica; obras de arte/joias = Arte, Joias e Coleções.

• Participações Societárias → subcategory ∈ {"Empresa operacional — sócio majoritário / controlador","Empresa operacional — sócio minoritário","Holding patrimonial pura","Holding mista (patrimonial + operacional)","Sociedade em Conta de Participação (SCP)","Participação em startup / empresa anjo","Mercado de Capitais","Participação em empresa no exterior (LLC, offshore, BVI, Cayman)","Trust no exterior (Lei 14.754/23)"}; subsubcategory = ""
  Dica: ações negociadas em bolsa (Petrobras, Vale, etc) = Mercado de Capitais; holding offshore = Participação em empresa no exterior.

• Aplicações e Investimentos → subcategory ∈ {"Renda Fixa","Fundos","Renda Variável","Alta Liquidez"}; subsubcategory:
  - Se "Renda Fixa": ∈ {"CDB / RDB","LCI / LCA (isentos de IR para PF)","LIG — Letra Imobiliária Garantida","LC — Letra de Câmbio","CRI / CRA (isentos de IR para PF)","Debêntures (quando ativo)","Debêntures incentivadas (infraestrutura — isentas de IR)","COE — Certificado de Operações Estruturadas","DPGE — Depósito a Prazo com Garantia Especial","Tesouro Selic / Prefixado / IPCA+"}
  - Se "Fundos": ∈ {"Fundo DI / Renda Fixa","Fundo Multimercado (FIM)","Fundo de Ações (FIA)","Fundo Cambial","FIP — Fundo de Investimento em Participações","FIDC — Fundo de Direitos Creditórios","FII — Fundo de Investimento Imobiliário","ETF (renda fixa ou variável)","Fundo de Investimento Exclusivo (FIE)","Fundo no Exterior / Fundo Offshore"}
  - Se "Renda Variável": ∈ {"Ações (B3 — custódia em corretora)","BDRs — Brazilian Depositary Receipts","ETF negociado em bolsa","Opções / derivativos","Contratos futuros (dólar, índice, commodities)"}
  - Se "Alta Liquidez": ∈ {"Poupança","Conta remunerada / CDB liquidez diária","Fundo DI com resgate D+0"}

• Previdência Privada → subcategory ∈ {"PGBL — deduz até 12% da renda bruta","VGBL — IR só sobre rendimentos","FAPI — Fundo de Aposentadoria Programada Individual","Previdência no exterior (401k, pension fund, plano estrangeiro)"}; subsubcategory = ""

• Créditos e Direitos → subcategory ∈ {"Empréstimos Concedidos","Recebíveis e Direitos"}; subsubcategory:
  - Se "Empréstimos Concedidos": ∈ {"Mútuo / empréstimo a sócio (AFAC ou contrato formal)","Mútuo / empréstimo a familiar","Mútuo / empréstimo a terceiros"}
  - Se "Recebíveis e Direitos": ∈ {"Conta a receber (venda parcelada)","Direito sobre imóvel (promessa, opção de compra)","Precatório / crédito judicial","Herança a receber / inventário em curso","Indenização a receber (trabalhista, cível)","Depósito caução / garantia de aluguel","Saldo do FGTS (código 40)","Consórcio contemplado ou não (código 95)","Crédito tributário a recuperar","Ativos em inventário (espólio)"}

• Contas Bancárias e Saldos → subcategory ∈ {"Conta corrente (banco nacional)","Conta poupança","Conta remunerada / CDB liquidez diária","Conta no exterior (saldo > US$ 1.000 em 31/12)","Conta em corretora no exterior (IB, Schwab...)","Conta em fintech / carteira digital"}; subsubcategory = ""

• Criptoativos → subcategory ∈ {"Bitcoin (BTC)","Ethereum (ETH)","Stablecoins (USDT, USDC, BRZ)","Altcoins diversas","Tokens de utilidade / governança","NFTs"}; subsubcategory = ""

• Remuneração Variável em Equity → subcategory ∈ {"Opções de Compra","Ações Restritas","Planos de Compra","Phantom / Sintéticos","Startups"}; subsubcategory:
  - Se "Opções de Compra": ∈ {"Stock Options (não exercida)","Stock Options exercidas","Warrants"}
  - Se "Ações Restritas": ∈ {"RSU — Restricted Stock Unit (em vesting)","RSU liquidada","RSA — Restricted Stock Award"}
  - Se "Planos de Compra": ∈ {"ESPP — Employee Stock Purchase Plan","Matching de ações pelo empregador"}
  - Se "Phantom / Sintéticos": ∈ {"Phantom Shares","SAR — Stock Appreciation Rights","Bônus atrelado a performance (cash-settled)"}
  - Se "Startups": ∈ {"Opção de compra em startup","Vesting em empresa não listada","SAFE — Simple Agreement for Future Equity","Nota conversível"}

DÍVIDAS (array "debts") — também classificadas com subcategory + subsubcategory + confidence:
  - "Financiamentos": ∈ {"Financiamento imobiliário (SFH, SFI, alienação fiduciária)","Financiamento de veículo / bem móvel"}
  - "Empréstimos": ∈ {"Empréstimo bancário (pessoal, consignado)","Empréstimo de pessoa física (sócio, familiar)","Empréstimo de pessoa jurídica (empresa do grupo)"}
  - "Outros Passivos": ∈ {"Debêntures emitidas","Parcelamento fiscal (REFIS)","Garantia prestada (aval, fiança)","Dívida no exterior"}

CONFIDENCE — Use "low" quando:
- A descrição é genérica ("Outros bens", "Investimento", "Cotas")
- Há ambiguidade entre 2+ opções
- Você teve que inferir o tipo por contexto fraco
Use "high" quando a descrição menciona claramente o instrumento ("CDB Banco BTG", "Apartamento Pinheiros", "Ações Petrobras", "BTC")."""

EXTRACT_SYSTEM = (
    "Especialista em declarações fiscais brasileiras. "
    "Retorne APENAS JSON válido e completo, sem texto adicional."
)


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        # Sempre true agora — usuário fornece a própria chave depois de logar.
        "user_provides_key": True,
        "auth_enabled": True,
    }


@app.post("/api/extract", dependencies=[Depends(auth)])
async def extract(
    dirpf: UploadFile | None = File(default=None),
    dcbe: UploadFile | None = File(default=None),
    x_anthropic_api_key: str | None = Header(default=None),
):
    # A chave da Anthropic agora vem do usuário, não do servidor. O frontend
    # coleta uma vez no login e envia em cada chamada via X-Anthropic-Api-Key.
    if not x_anthropic_api_key or not x_anthropic_api_key.startswith("sk-ant-"):
        raise HTTPException(
            status_code=400,
            detail="Forneça uma API key válida da Anthropic (formato sk-ant-...). Vá em Configurações para atualizar.",
        )
    if not dirpf and not dcbe:
        raise HTTPException(status_code=400, detail="at least one of dirpf/dcbe must be uploaded")

    content: list[dict[str, Any]] = []
    for f, title in ((dirpf, "DIRPF 2025"), (dcbe, "DCBE 2025")):
        if not f:
            continue
        raw = await f.read()
        if not raw:
            continue
        b64 = base64.b64encode(raw).decode("ascii")
        content.append({
            "type": "document",
            "source": {"type": "base64", "media_type": "application/pdf", "data": b64},
            "title": title,
        })
    content.append({"type": "text", "text": EXTRACT_PROMPT})

    payload = {
        "model": ANTHROPIC_MODEL,
        "max_tokens": 32000,
        "system": EXTRACT_SYSTEM,
        "messages": [{"role": "user", "content": content}],
    }
    headers = {
        "x-api-key": x_anthropic_api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout=280.0) as client:
            resp = await client.post(ANTHROPIC_URL, json=payload, headers=headers)
    except httpx.RequestError as e:
        raise HTTPException(status_code=502, detail=f"upstream error: {e}") from e

    if resp.status_code != 200:
        log.error(f"anthropic returned {resp.status_code}: {resp.text[:400]}")
        raise HTTPException(
            status_code=502,
            detail=f"anthropic returned {resp.status_code}: {resp.text[:300]}",
        )

    result = resp.json()
    if "error" in result:
        raise HTTPException(status_code=502, detail=f"anthropic error: {result['error']}")

    raw_text = ""
    for blk in result.get("content", []):
        if blk.get("type") == "text":
            raw_text += blk.get("text", "")
    if not raw_text:
        raise HTTPException(
            status_code=502,
            detail=f"anthropic returned no text; stop_reason={result.get('stop_reason')}",
        )

    cleaned = re.sub(r"^\s*```json\s*", "", raw_text)
    cleaned = re.sub(r"\s*```\s*$", "", cleaned).strip()
    if result.get("stop_reason") == "max_tokens":
        last_brace = cleaned.rfind("}")
        if last_brace != -1:
            cleaned = cleaned[: last_brace + 1]
        opens_sq = cleaned.count("[") - cleaned.count("]")
        opens_br = cleaned.count("{") - cleaned.count("}")
        cleaned += "]" * max(0, opens_sq) + "}" * max(0, opens_br)

    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError as e:
        log.error(f"json parse failed: {e}\nresponse head: {cleaned[:500]}")
        raise HTTPException(status_code=502, detail=f"could not parse JSON from anthropic: {e}") from e

    return parsed


class BuildBody(BaseModel):
    client: str = ""
    cpf: str = ""
    year: int = 2024
    spouse: dict[str, Any] = {}
    dependents: list[dict[str, Any]] = []
    groups: list[dict[str, Any]] = []
    debts: list[dict[str, Any]] = []

    class Config:
        extra = "allow"


def _safe_filename(client: str, kind: str, ext: str) -> str:
    base = re.sub(r"[^A-Za-z0-9_-]+", "_", (client or "client").upper())[:60].strip("_")
    return f"{base}_{kind}.{ext}"


@app.post("/api/build/deck", dependencies=[Depends(auth)])
def build_deck_endpoint(body: BuildBody):
    data = body.model_dump()
    tmp_dir = Path(tempfile.mkdtemp(prefix="hsa_"))
    out_path = tmp_dir / f"{uuid.uuid4().hex}.pptx"
    try:
        ok = deck_builder.build_deck(data, str(out_path))
    except Exception as e:
        log.exception("build_deck failed")
        raise HTTPException(status_code=500, detail=f"deck build failed: {e}") from e
    if not ok or not out_path.exists():
        raise HTTPException(status_code=500, detail="deck build returned no output")

    return FileResponse(
        out_path,
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        filename=_safe_filename(data.get("client", ""), "PATRIMON_IA", "pptx"),
    )


@app.post("/api/build/excel", dependencies=[Depends(auth)])
def build_excel_endpoint(body: BuildBody):
    data = body.model_dump()
    tmp_dir = Path(tempfile.mkdtemp(prefix="hsa_"))
    out_path = tmp_dir / f"{uuid.uuid4().hex}.xlsx"
    try:
        ok = excel_builder.build_excel(data, str(out_path))
    except Exception as e:
        log.exception("build_excel failed")
        raise HTTPException(status_code=500, detail=f"excel build failed: {e}") from e
    if not ok or not out_path.exists():
        raise HTTPException(status_code=500, detail="excel build returned no output")

    return FileResponse(
        out_path,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=_safe_filename(data.get("client", ""), "LISTA_ATIVOS", "xlsx"),
    )


# ── isolated single-slide exports ────────────────────────────────────────
# These build the full 6-slide deck then strip everything except the
# requested slide (5 = patrimonial orgchart, 6 = family orgchart).
def _build_single_slide(data: dict, keep_idx: int, kind: str) -> Path:
    from pptx import Presentation
    tmp_dir = Path(tempfile.mkdtemp(prefix="hsa_"))
    full_path = tmp_dir / f"_full_{uuid.uuid4().hex}.pptx"
    out_path  = tmp_dir / f"{uuid.uuid4().hex}.pptx"

    ok = deck_builder.build_deck(data, str(full_path))
    if not ok or not full_path.exists():
        raise HTTPException(status_code=500, detail=f"{kind} build failed (full deck step)")

    prs = Presentation(str(full_path))
    sldIdLst = prs.slides._sldIdLst
    ids = list(sldIdLst)
    if keep_idx >= len(ids):
        raise HTTPException(status_code=500, detail=f"deck has only {len(ids)} slides, cannot keep slide {keep_idx+1}")
    keep = ids[keep_idx]
    for sld in ids:
        if sld is not keep:
            sldIdLst.remove(sld)
    prs.save(str(out_path))
    return out_path


@app.post("/api/build/orgchart-patrimonial", dependencies=[Depends(auth)])
def build_orgchart_patrimonial_endpoint(body: BuildBody):
    data = body.model_dump()
    try:
        out_path = _build_single_slide(data, keep_idx=3, kind="orgchart-patrimonial")
    except HTTPException:
        raise
    except Exception as e:
        log.exception("build_orgchart_patrimonial failed")
        raise HTTPException(status_code=500, detail=f"orgchart-patrimonial failed: {e}") from e
    return FileResponse(
        out_path,
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        filename=_safe_filename(data.get("client", ""), "ORGANOGRAMA_PATRIMONIAL", "pptx"),
    )

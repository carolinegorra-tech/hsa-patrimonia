"""
HSA Patrimon.IA — FastAPI app for Vercel Python runtime.

Vercel routes any path starting with /api/* to this file (via vercel.json).
Everything else (the frontend) is served as a static asset by Vercel's CDN
from the /public folder.

Auth model:
  • Senha do escritório: HARDCODED como "humberto"
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

# deck_builder, excel_builder e checklist_builder vivem em api/lib/
import sys, os as _os_path
sys.path.insert(0, _os_path.path.join(_os_path.path.dirname(__file__), "lib"))
import deck_builder
import excel_builder
import checklist_builder

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
2. Se a soma dos itens individuais não bater exatamente com o "Total Grupo X" do DIRPF, mantenha os valores individuais como foram declarados.

3. JURISDIÇÃO — Defina pela LOCALIZAÇÃO REAL do ativo (campo "País" da DIRPF), NÃO pelo documento de origem:
   - jurisdiction = "Brasil"   → ativo no Brasil (campo País = "Brasil" / código 105)
   - jurisdiction = "Offshore" → ativo no exterior (qualquer outro país)

   ⚠ ATENÇÃO MÁXIMA: O DIRPF declara o patrimônio GLOBAL em BRL — INCLUI ativos no exterior. NÃO assuma que tudo que vem do DIRPF é "Brasil". Olhe o campo "País" de CADA item antes de classificar.

4. MERGE DIRPF + DCBE — Quando o MESMO ativo offshore aparece nos DOIS documentos, UNA em UM ÚNICO item:
   - jurisdiction: "Offshore"
   - dirpf: valor em R$ (vindo da DIRPF)
   - dcbe: valor em USD (vindo da DCBE)
   - desc: nome da entidade (use a versão mais completa entre os dois documentos)
   - loc: país de localização

5. dirpf = valor em R$ da DIRPF; dcbe = valor em USD da DCBE
6. Inclua dívidas da Ficha 8 no array "debts"
7. Inclua cônjuge da Ficha 2 em "spouse"; dependentes da Ficha 3
8. JSON 100% completo e fechado. Valores SEMPRE numéricos com centavos exatos.

CLASSIFICAÇÃO OBRIGATÓRIA (3 níveis) — Para cada item, ESCOLHA OBRIGATORIAMENTE a melhor opção:
- name: grupo (nível 1)
- subcategory: subcategoria do grupo (nível 2)
- subsubcategory: instrumento/sub-item (nível 3) — só preenche se a subcategoria tiver sub-itens
- confidence: "high" se a descrição deixa CLARO; "low" se você teve que CHUTAR.

GRUPOS válidos para "name":
"Bens Imóveis" | "Bens Móveis" | "Participações Societárias" | "Aplicações e Investimentos" | "Previdência Privada" | "Créditos e Direitos" | "Contas Bancárias e Saldos" | "Criptoativos" | "Remuneração Variável em Equity"
"""

EXTRACT_SYSTEM = (
    "Especialista em declarações fiscais brasileiras. "
    "Retorne APENAS JSON válido e completo, sem texto adicional."
)


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "user_provides_key": True,
        "auth_enabled": True,
    }


@app.post("/api/extract", dependencies=[Depends(auth)])
async def extract(
    dirpf: UploadFile | None = File(default=None),
    dcbe: UploadFile | None = File(default=None),
    x_anthropic_api_key: str | None = Header(default=None),
):
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


# ── NEW: Document checklist endpoint ──────────────────────────────────────
@app.post("/api/build/document-checklist", dependencies=[Depends(auth)])
def build_document_checklist_endpoint(body: BuildBody):
    """
    Gera o documento "Lista Inicial de Documentos" da HSA preenchido com:
      - nome do cliente no título e ao longo do texto
      - status "Concluído" (verde) ou "Pendente" (vermelho) ao final de
        cada um dos 12 itens da lista
    Espera receber `file_status` (dict) no body com as 12 keys do frontend.
    """
    data = body.model_dump()
    client_name = (data.get("client") or "").strip() or "Cliente"
    file_status = data.get("file_status") or {}
    if not isinstance(file_status, dict):
        raise HTTPException(status_code=400, detail="file_status must be a JSON object")

    tmp_dir = Path(tempfile.mkdtemp(prefix="hsa_"))
    out_path = tmp_dir / f"{uuid.uuid4().hex}.docx"
    try:
        checklist_builder.build_checklist(client_name, file_status, str(out_path))
    except Exception as e:
        log.exception("build_checklist failed")
        raise HTTPException(status_code=500, detail=f"checklist build failed: {e}") from e
    if not out_path.exists():
        raise HTTPException(status_code=500, detail="checklist build returned no output")

    return FileResponse(
        out_path,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename=_safe_filename(client_name, "LISTA_DOCUMENTOS", "docx"),
    )


# ── isolated single-slide exports ────────────────────────────────────────
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


@app.post("/api/build/orgchart-familiar", dependencies=[Depends(auth)])
def build_orgchart_familiar_endpoint(body: BuildBody):
    data = body.model_dump()
    try:
        out_path = _build_single_slide(data, keep_idx=4, kind="orgchart-familiar")
    except HTTPException:
        raise
    except Exception as e:
        log.exception("build_orgchart_familiar failed")
        raise HTTPException(status_code=500, detail=f"orgchart-familiar failed: {e}") from e
    return FileResponse(
        out_path,
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        filename=_safe_filename(data.get("client", ""), "ORGANOGRAMA_FAMILIAR", "pptx"),
    )

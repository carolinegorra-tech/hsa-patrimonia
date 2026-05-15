"""
HSA Patrimon.IA — FastAPI app for Vercel Python runtime.

Vercel routes any path starting with /api/* to this file (via vercel.json).
Everything else (the frontend) is served as a static asset by Vercel's CDN
from the /public folder — we do NOT mount static here.

Env vars (set in the Vercel dashboard):
  ANTHROPIC_API_KEY   required
  HSA_PASSWORD        optional shared password
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

# These two are siblings of this file inside /api on Vercel
import deck_builder
import excel_builder

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
HSA_PASSWORD      = os.environ.get("HSA_PASSWORD", "")
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
    if not HSA_PASSWORD:
        return
    if x_hsa_password != HSA_PASSWORD:
        raise HTTPException(status_code=401, detail="invalid or missing password")


EXTRACT_PROMPT = """Extraia todos os bens, direitos e informações familiares deste(s) documento(s) e retorne APENAS JSON válido (sem markdown, sem ```):
{"client":"NOME COMPLETO","cpf":"000.000.000-00","year":2024,"spouse":{"name":"","cpf":"","marriage_regime":"","marriage_date":"","certificate_registry":""},"dependents":[{"name":"","cpf":"","birth_date":"","relationship":""}],"groups":[{"name":"categoria","jurisdiction":"Brasil ou Offshore","items":[{"id":1,"desc":"descrição do ativo","loc":"cidade/país","dirpf":valor_numerico_ou_null,"dcbe":valor_numerico_ou_null,"comments":""}]}],"debts":[{"id":1,"desc":"descrição da dívida","value":valor_numerico}]}

REGRAS CRÍTICAS:
1. DIRPF — use SEMPRE o valor do resumo por grupo (ex: "Total Grupo 01 Bens Imóveis = R$ 45.340.841,37"). NÃO some itens individuais — use o total oficial do grupo diretamente.
2. Se um grupo tem itens individuais E um total, crie UM item por grupo usando o TOTAL OFICIAL.
3. Grupos Brasil: Imóveis, Ações, Participações Societárias, Fundos de Investimento, Investimentos Renda Fixa, Obras de Arte, Veículos, Contas Bancárias, Créditos, Seguros, Títulos, Empréstimos
4. jurisdiction = "Brasil" ou "Offshore"
5. dirpf = valor em R$ da DIRPF, dcbe = valor em USD da DCBE
6. Inclua dívidas da Ficha 8 no array "debts"
7. Inclua cônjuge/companheiro(a) da Ficha 2 no campo "spouse" (deixe vazio "" se não houver)
8. Inclua dependentes da Ficha 3 no array "dependents" (deixe [] se não houver)
9. JSON 100% completo e fechado. Valores SEMPRE numéricos com centavos exatos."""

EXTRACT_SYSTEM = (
    "Especialista em declarações fiscais brasileiras. "
    "Retorne APENAS JSON válido e completo, sem texto adicional."
)


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "anthropic_configured": bool(ANTHROPIC_API_KEY),
        "auth_enabled": bool(HSA_PASSWORD),
    }


@app.post("/api/extract", dependencies=[Depends(auth)])
async def extract(
    dirpf: UploadFile | None = File(default=None),
    dcbe: UploadFile | None = File(default=None),
):
    if not ANTHROPIC_API_KEY:
        raise HTTPException(status_code=500, detail="server not configured: missing ANTHROPIC_API_KEY")
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
        "max_tokens": 16000,
        "system": EXTRACT_SYSTEM,
        "messages": [{"role": "user", "content": content}],
    }
    headers = {
        "x-api-key": ANTHROPIC_API_KEY,
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

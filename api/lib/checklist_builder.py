"""
checklist_builder.py — Gera um .docx simples sem deps externas.

Versão MÍNIMA: usa só zipfile + strings (sem python-docx, sem template
embutido). Um .docx é só um zip com XML dentro — esta versão constrói os
arquivos XML necessários manualmente.

Vantagens:
  - Não depende de python-docx (que pode não estar instalado no Vercel)
  - Arquivo Python pequeno (~150 linhas)
  - Sem template embutido (sem base64 gigante)
  - Import muito leve (só zipfile + io da stdlib)

Args do build_checklist:
  - client_name: nome completo do cliente
  - file_status: dict {key: bool} com as 12 keys
  - output_path: onde salvar o .docx
"""
from __future__ import annotations

import io
import zipfile


_ITEMS = [
    ("certidao",
     'Cópia da certidão de casamento de {NAME} ("{FIRST}") e esposa, bem como de eventual pacto antenupcial entre eles, se aplicável.'),
    ("familia",
     'Informações relevantes sobre a estrutura familiar de {FIRST} e esposa, incluindo nome e idade dos filhos, netos e respectivos estados civis.'),
    ("dirpf",
     'Declaração(ões) de Imposto de Renda sobre a Pessoa Física ("DIRPF") de {FIRST} e esposa, ano-calendário 2024 e/ou rascunho da DIRPF referente ao ano-calendário 2025.'),
    ("dcbe",
     'Declaração(ões) de Capitais Brasileiros no Exterior ("DCBE") mais recente entregue ao Banco Central por {FIRST} e esposa, conforme aplicável.'),
    ("alteracoes",
     'Lista de alterações patrimoniais relevantes ocorridas no decorrer dos anos de 2025 e 2026 e/ou com previsão de materialização no curto/médio prazo, incluindo ativos com expectativa de recebimento.'),
    ("societario_br",
     'Se aplicável, organograma e documentos societários (contratos sociais, estatutos, atas), balanço patrimonial mais recente e documentos que indiquem as regras de governança de sociedades investidas por {FIRST} e esposa no Brasil.'),
    ("societario_off",
     'Organograma e documentos societários dos veículos offshore detidos por {FIRST} e esposa, incluindo sociedades, fundos e trusts (Memorandum and Articles of Association, Register of Members, Trust Deed).'),
    ("lei_14754",
     'Informações quanto ao tratamento tributário aplicável aos eventuais veículos controlados no exterior por {FIRST} e esposa, especificamente para fins da Lei nº 14.754/23, se aplicável.'),
    ("imoveis",
     'Informações sobre a destinação de uso e fluxo de rendimentos dos imóveis detidos por {FIRST} e esposa, conforme aplicável.'),
    ("emprestimos",
     'Informações sobre eventuais empréstimos concedidos ou tomados por {FIRST} e esposa, em vigor, conforme aplicável.'),
    ("doacoes",
     'Informações sobre eventuais doações ou heranças recebidas ou realizadas por {FIRST} e esposa, incluindo ITCMD aplicável.'),
    ("previdencia",
     'Informações sobre planos de previdência privada (VGBL/PGBL) e seguros de vida detidos por {FIRST} e esposa, no Brasil e no exterior, conforme aplicável.'),
]


def _esc(s: str) -> str:
    return (s.replace("&", "&amp;")
              .replace("<", "&lt;")
              .replace(">", "&gt;")
              .replace('"', "&quot;"))


# ── Static parts of a .docx package ──────────────────────────────────
_CONTENT_TYPES = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
<Default Extension="xml" ContentType="application/xml"/>
<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
</Types>'''

_RELS = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>'''

_DOC_RELS = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"></Relationships>'''


def _para(text: str, *, bold: bool = False, size_half_pt: int = 22,
          color: str = "000000", align: str = "left") -> str:
    """Build a Word paragraph XML."""
    bold_xml = '<w:b/><w:bCs/>' if bold else ''
    align_xml = f'<w:jc w:val="{align}"/>' if align != "left" else ''
    return (
        f'<w:p><w:pPr>{align_xml}<w:spacing w:after="120"/></w:pPr>'
        f'<w:r><w:rPr>{bold_xml}<w:sz w:val="{size_half_pt}"/>'
        f'<w:color w:val="{color}"/></w:rPr>'
        f'<w:t xml:space="preserve">{_esc(text)}</w:t></w:r></w:p>'
    )


def _item_para(idx: int, text: str, is_done: bool) -> str:
    """Build a numbered item paragraph with status at the end."""
    status_label = "Concluído" if is_done else "Pendente"
    status_color = "2E8B57" if is_done else "C8102E"  # green / red
    return (
        '<w:p><w:pPr><w:spacing w:after="200"/>'
        '<w:ind w:left="567" w:hanging="567"/></w:pPr>'
        # number
        f'<w:r><w:rPr><w:sz w:val="22"/></w:rPr>'
        f'<w:t xml:space="preserve">{idx}.\t</w:t></w:r>'
        # body text
        f'<w:r><w:rPr><w:sz w:val="22"/></w:rPr>'
        f'<w:t xml:space="preserve">{_esc(text)}</w:t></w:r>'
        # status
        f'<w:r><w:rPr><w:b/><w:bCs/><w:sz w:val="22"/>'
        f'<w:color w:val="{status_color}"/></w:rPr>'
        f'<w:t xml:space="preserve">  — {status_label}</w:t></w:r>'
        '</w:p>'
    )


def _build_document_xml(client_name: str, file_status: dict) -> str:
    name_upper = (client_name or "Cliente").upper().strip()
    first = name_upper.split()[0] if name_upper else "CLIENTE"

    body_parts: list[str] = []

    # Header
    body_parts.append(_para("HUMBERTO SANCHES", bold=True, size_half_pt=36,
                            color="283944", align="center"))
    body_parts.append(_para("+ ASSOCIADOS", bold=True, size_half_pt=18,
                            color="8E959B", align="center"))
    body_parts.append(_para("", align="center"))

    # Title
    body_parts.append(_para(name_upper, bold=True, size_half_pt=24, align="center"))
    body_parts.append(_para("PLANEJAMENTO PATRIMONIAL E SUCESSÓRIO", align="center"))
    body_parts.append(_para("LISTA INICIAL: INFORMAÇÕES / DOCUMENTAÇÃO DE SUPORTE",
                            align="center"))
    body_parts.append(_para(""))

    # Items
    for idx, (key, template) in enumerate(_ITEMS, start=1):
        is_done = bool(file_status.get(key, False))
        text = template.replace("{NAME}", name_upper).replace("{FIRST}", first)
        body_parts.append(_item_para(idx, text, is_done))

    body_parts.append(_para(""))

    # Section properties (page size, margins)
    sect = (
        '<w:sectPr>'
        '<w:pgSz w:w="11906" w:h="16838"/>'
        '<w:pgMar w:top="1417" w:right="1701" w:bottom="1417" w:left="1701" '
        'w:header="708" w:footer="708" w:gutter="0"/>'
        '</w:sectPr>'
    )

    document = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        '<w:body>'
        + "".join(body_parts)
        + sect +
        '</w:body></w:document>'
    )
    return document


def build_checklist(client_name: str, file_status: dict, output_path: str) -> str:
    """Gera o checklist .docx."""
    file_status = file_status or {}
    doc_xml = _build_document_xml(client_name, file_status)

    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", _CONTENT_TYPES)
        zf.writestr("_rels/.rels", _RELS)
        zf.writestr("word/_rels/document.xml.rels", _DOC_RELS)
        zf.writestr("word/document.xml", doc_xml)

    return output_path

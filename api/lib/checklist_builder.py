"""
checklist_builder.py — Gera um .docx "Lista Inicial de Documentos" sem deps.

Constrói o .docx do zero usando apenas a stdlib (zipfile + strings XML).
NÃO depende de python-docx. Um .docx é só um zip com 4 arquivos XML —
esta versão monta esses arquivos manualmente.

Vantagens:
  - Zero deps externas (não precisa estar em requirements.txt)
  - Arquivo pequeno (~200 linhas)
  - Import super leve (zipfile + io da stdlib)
  - Não tem como o Vercel reclamar de import

API:
  build_checklist(client_name: str, file_status: dict, output_path: str) -> str

  client_name: nome completo do cliente (ex: "Marcelo Bueno Andrade")
              Use "Cliente" como placeholder antes do nome ser extraído.
  file_status: dict {key: bool} — True = Concluído, False/missing = Pendente
              keys: certidao, familia, dirpf, dcbe, alteracoes,
                    societario_br, societario_off, lei_14754,
                    imoveis, emprestimos, doacoes, previdencia
  output_path: caminho onde salvar o .docx
"""
from __future__ import annotations

import zipfile
from xml.sax.saxutils import escape as _xml_escape


# Ordem fixa dos 12 itens (igual ao template original Jane Doe)
_ITEMS = [
    ("certidao",
     'Cópia da certidão de casamento de {NAME} ("{FIRST}") e esposa, '
     'bem como de eventual pacto antenupcial entre eles, se aplicável.'),
    ("familia",
     'Informações relevantes sobre a estrutura familiar de {FIRST} e esposa, '
     'incluindo nome e idade dos filhos, netos e respectivos estados civis.'),
    ("dirpf",
     'Declaração(ões) de Imposto de Renda sobre a Pessoa Física ("DIRPF") '
     'de {FIRST} e esposa, ano-calendário 2024 e/ou rascunho da DIRPF '
     'referente ao ano-calendário 2025.'),
    ("dcbe",
     'Declaração(ões) de Capitais Brasileiros no Exterior ("DCBE") mais '
     'recente entregue ao Banco Central por {FIRST} e esposa, conforme aplicável.'),
    ("alteracoes",
     'Lista de alterações patrimoniais relevantes ocorridas no decorrer dos '
     'anos de 2025 e 2026 e/ou com previsão de materialização no curto/médio '
     'prazo, incluindo ativos com expectativa de recebimento.'),
    ("societario_br",
     'Se aplicável, organograma e documentos societários (contratos sociais, '
     'estatutos, atas), balanço patrimonial mais recente e documentos que '
     'indiquem as regras de governança de sociedades investidas por {FIRST} '
     'e esposa no Brasil, e os respectivos percentuais de participação em '
     'cada veículo. Favor incluir informações sobre as atividades '
     'desempenhadas por cada sociedade (i.e., se operacional (indicar ramo '
     'de atividade), holding patrimonial, inativa etc.).'),
    ("societario_off",
     'Organograma e documentos societários dos veículos offshore detidos por '
     '{FIRST} e esposa, incluindo sociedades, fundos e trusts, tais como '
     'Memorandum and Articles of Association, Register of Members, Register '
     'of Directors e Trust Deed, conforme aplicável.'),
    ("lei_14754",
     'Informações quanto ao tratamento tributário aplicável aos eventuais '
     'veículos controlados no exterior por {FIRST} e esposa, especificamente '
     'para fins da Lei nº 14.754/23, se aplicável.'),
    ("imoveis",
     'Informações relevantes sobre os imóveis detidos por {FIRST} e esposa, '
     'tais como destinação de uso (residência, lazer, locação etc.) e fluxo '
     'de rendimentos auferidos, se aplicável.'),
    ("emprestimos",
     'Informações sobre eventuais empréstimos concedidos ou tomados por '
     '{FIRST} e esposa, atualmente em vigor.'),
    ("doacoes",
     'Informações sobre eventuais doações e/ou heranças recebidas e/ou '
     'realizadas por {FIRST} e esposa, incluindo o ITCMD recolhido.'),
    ("previdencia",
     'Informações sobre eventuais planos de previdência (VGBL/PGBL) e '
     'seguros de vida contratados por {FIRST} e esposa, no Brasil e/ou no '
     'exterior.'),
]


# ───────────────────────── XML helpers ─────────────────────────

def _esc(s: str) -> str:
    return _xml_escape(s, {'"': "&quot;", "'": "&apos;"})


def _para_run(text: str, *, bold: bool = False, size_half_pt: int = 22,
              color: str = "000000", font: str = "Calibri") -> str:
    """Build a single <w:r> run with formatting."""
    rpr_bits = [f'<w:rFonts w:ascii="{font}" w:hAnsi="{font}"/>']
    if bold:
        rpr_bits.append('<w:b/><w:bCs/>')
    rpr_bits.append(f'<w:color w:val="{color}"/>')
    rpr_bits.append(f'<w:sz w:val="{size_half_pt}"/><w:szCs w:val="{size_half_pt}"/>')
    rpr = '<w:rPr>' + ''.join(rpr_bits) + '</w:rPr>'
    return f'<w:r>{rpr}<w:t xml:space="preserve">{_esc(text)}</w:t></w:r>'


def _para(runs: list[str], *, align: str = "left",
          spacing_after: int = 200, indent_left: int = 0,
          numbered: bool = False) -> str:
    """Wrap runs in a <w:p> paragraph."""
    ppr_bits = []
    if numbered:
        ppr_bits.append('<w:numPr><w:ilvl w:val="0"/><w:numId w:val="1"/></w:numPr>')
    ppr_bits.append(f'<w:spacing w:after="{spacing_after}" w:line="276" w:lineRule="auto"/>')
    if indent_left:
        ppr_bits.append(f'<w:ind w:left="{indent_left}" w:hanging="360"/>')
    if align == "center":
        ppr_bits.append('<w:jc w:val="center"/>')
    elif align == "right":
        ppr_bits.append('<w:jc w:val="right"/>')
    elif align == "both":
        ppr_bits.append('<w:jc w:val="both"/>')
    ppr = '<w:pPr>' + ''.join(ppr_bits) + '</w:pPr>'
    return f'<w:p>{ppr}{"".join(runs)}</w:p>'


def _build_document_xml(client_name: str, file_status: dict) -> str:
    name = (client_name or "Cliente").strip() or "Cliente"
    first = name.split()[0] if name != "Cliente" else "Cliente"
    name_upper = name.upper()

    paragraphs = []

    # Header — firm name (centered, bold, navy)
    paragraphs.append(_para([
        _para_run("HUMBERTO SANCHES + ASSOCIADOS",
                  bold=True, size_half_pt=20, color="283944"),
    ], align="center", spacing_after=60))

    paragraphs.append(_para([
        _para_run("Advogados", size_half_pt=18, color="8E959B"),
    ], align="center", spacing_after=480))

    # Title
    paragraphs.append(_para([
        _para_run(f"{name_upper}", bold=True, size_half_pt=28, color="283944"),
    ], align="center", spacing_after=120))

    paragraphs.append(_para([
        _para_run("Lista Inicial de Documentos", size_half_pt=24,
                  color="283944"),
    ], align="center", spacing_after=480))

    # Intro paragraph
    paragraphs.append(_para([
        _para_run(
            f"Prezado(a) {first}, segue lista de documentos e informações "
            f"que precisaremos receber para iniciarmos a análise patrimonial "
            f"da família. Os itens marcados como ",
            size_half_pt=22),
        _para_run("Concluído", bold=True, size_half_pt=22, color="2E7D32"),
        _para_run(" já foram recebidos; os marcados como ", size_half_pt=22),
        _para_run("Pendente", bold=True, size_half_pt=22, color="C62828"),
        _para_run(" seguem em aberto.", size_half_pt=22),
    ], align="both", spacing_after=360))

    # 12 numbered items
    for i, (key, template) in enumerate(_ITEMS, start=1):
        text = template.replace("{NAME}", name).replace("{FIRST}", first)
        done = bool(file_status.get(key, False))
        status_label = "Concluído" if done else "Pendente"
        status_color = "2E7D32" if done else "C62828"

        paragraphs.append(_para([
            _para_run(f"{i}. ", bold=True, size_half_pt=22),
            _para_run(text, size_half_pt=22),
            _para_run("  —  ", size_half_pt=22),
            _para_run(status_label, bold=True, size_half_pt=22,
                      color=status_color),
        ], align="both", spacing_after=200, indent_left=360))

    # Footer-ish closing
    paragraphs.append(_para([
        _para_run("Ficamos à disposição para esclarecimentos.",
                  size_half_pt=22, color="283944"),
    ], align="left", spacing_after=120))

    body = "".join(paragraphs)

    return f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body>
    {body}
    <w:sectPr>
      <w:pgSz w:w="12240" w:h="15840"/>
      <w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="1440"
               w:header="720" w:footer="720" w:gutter="0"/>
    </w:sectPr>
  </w:body>
</w:document>'''


# ───────────────────────── Static XML files ─────────────────────────

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
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
</Relationships>'''


# ───────────────────────── Public API ─────────────────────────

def build_checklist(client_name: str, file_status: dict | None,
                    output_path: str) -> str:
    """Generate the document checklist .docx at output_path."""
    file_status = file_status or {}
    doc_xml = _build_document_xml(client_name, file_status)

    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", _CONTENT_TYPES)
        zf.writestr("_rels/.rels", _RELS)
        zf.writestr("word/_rels/document.xml.rels", _DOC_RELS)
        zf.writestr("word/document.xml", doc_xml)

    return output_path

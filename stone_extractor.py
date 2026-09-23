import re

import pdfplumber


def _valor(txt):
    if not txt:
        return 0.0
    txt = txt.strip().replace('R$', '').replace(' ', '')
    txt = txt.replace('.', '').replace(',', '.')
    try:
        return float(txt)
    except Exception:
        return 0.0


def extract_vendas_stone(pdf_path):
    """Le o relatorio 'Resumo de vendas' da Stone (consolidado mensal).

    Esse relatorio nao tem tabelas com grade (pdfplumber.extract_tables()
    nao acha nada), entao a extracao e por regex ancorado nos rotulos fixos
    do relatorio, que sao bem especificos.
    """
    result = {
        'razao_social': '',
        'documento': '',
        'periodo_inicio': '',
        'periodo_fim': '',
        'total_vendido': 0.0,
        'vendas_realizadas': 0,
        'ticket_medio': 0.0,
        'canceladas': 0.0,
        'contestadas': 0.0,
        'devolvidos': 0.0,
        'credito': 0.0,
        'debito': 0.0,
        'pix_maquininha': 0.0,
        'voucher': 0.0,
    }

    with pdfplumber.open(pdf_path) as pdf:
        full_text = pdf.pages[0].extract_text() or ''

    m = re.search(r'^(.+?)\s+(\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2})\s*$', full_text, re.MULTILINE)
    if m:
        result['razao_social'] = m.group(1).strip()
        result['documento'] = m.group(2)

    m = re.search(
        r'R\$\s*([\d.,]+)\s+(\d+)\s*vendas\s+R\$\s*([\d.,]+)',
        full_text
    )
    if m:
        result['total_vendido'] = _valor(m.group(1))
        result['vendas_realizadas'] = int(m.group(2))
        result['ticket_medio'] = _valor(m.group(3))

    m = re.search(
        r'Canceladas\s+Contestadas\s+Devolvidos\s+Pix\s*\n((?:R\$\s*[\d.,]+\s*)+)',
        full_text
    )
    if m:
        vals = re.findall(r'R\$\s*([\d.,]+)', m.group(1))
        if len(vals) > 0:
            result['canceladas'] = _valor(vals[0])
        if len(vals) > 1:
            result['contestadas'] = _valor(vals[1])
        if len(vals) > 2:
            result['devolvidos'] = _valor(vals[2])

    m = re.search(
        r'Cr[eé]dito\s+D[eé]bito\s+Pix na maquininha\s+Voucher\s*\n((?:R\$\s*[\d.,]+\s*)+)',
        full_text
    )
    if m:
        vals = re.findall(r'R\$\s*([\d.,]+)', m.group(1))
        if len(vals) > 0:
            result['credito'] = _valor(vals[0])
        if len(vals) > 1:
            result['debito'] = _valor(vals[1])
        if len(vals) > 2:
            result['pix_maquininha'] = _valor(vals[2])
        if len(vals) > 3:
            result['voucher'] = _valor(vals[3])

    m = re.search(
        r'Per[ií]odo:\s*de\s*(\d{2}/\d{2}/\d{2,4})\s*a\s*(\d{2}/\d{2}/\d{2,4})',
        full_text, re.IGNORECASE
    )
    if m:
        result['periodo_inicio'] = m.group(1)
        result['periodo_fim'] = m.group(2)

    return result

import pdfplumber
import re

ALIAS_FECHADORES = {
    'EDEM': 'EDEMILSON',
    'EDEMILS': 'EDEMILSON',
    'EDEMILSON': 'EDEMILSON',
    'ALE': 'ALESSANDRA',
    'ALESSANDRA': 'ALESSANDRA',
    'ERIK': 'ERIK',
    'DEISE': 'DEISE',
    'RICHARD': 'RICHARD',
}

UNIDADE_MAP = {
    'OK INN HOTEL TUBARAO': 'Ok Inn Tubarao',
    'OK INN EXPRESS TUBARAO': 'Ok Inn Express Tubarao',
    'OK INN TUBARAO': 'Ok Inn Tubarao',
    'OK INN EXPRESS': 'Ok Inn Express Tubarao',
    'CRICIUMA EXPRESS': 'Criciuma Express',
    'CRICIUMA CENTRO': 'Criciuma Centro',
    'FLORIPA COQUEIROS': 'Floripa Coqueiros',
    'ATLANTICO SUL': 'Atlantico Sul',
    'RENASCENCA': 'Renascenca',
    'YOU HI 01': 'You HI 01',
    'YOU HI': 'You HI 01',
}


def normalizar_valor(val_str):
    if not val_str:
        return 0.0
    val_str = val_str.strip().replace('R$', '').replace(' ', '')
    val_str = val_str.replace('.', '').replace(',', '.')
    try:
        return float(val_str)
    except Exception:
        return 0.0


def resolver_unidade(texto):
    texto_upper = texto.upper().strip()
    for key, val in UNIDADE_MAP.items():
        if key in texto_upper:
            return val
    return texto.strip()


def resolver_fechador(nome):
    nome_upper = nome.upper().strip()
    for key, val in ALIAS_FECHADORES.items():
        if key in nome_upper:
            return val
    return nome.strip()


def extract_caixa_data(pdf_path):
    result = {
        'unidade': '',
        'data_fechamento': '',
        'quem_fechou': '',
        'movimento_num': '',
        'dinheiro_saida': 0.0,
        'dinheiro_encerramento': 0.0,
        'faturado': 0.0,
        'uso_credito': 0.0,
        'deposito_bancario': 0.0,
        'cartao': 0.0,
        'cortesia': 0.0,
    }

    full_text = ''
    pdf = pdfplumber.open(pdf_path)
    for page in pdf.pages:
        full_text += (page.extract_text() or '') + '\n'
    pdf.close()

    lines = full_text.split('\n')

    for line in lines[:10]:
        line_stripped = line.strip()
        if line_stripped and len(line_stripped) > 5:
            unidade = resolver_unidade(line_stripped)
            if unidade != line_stripped:
                result['unidade'] = unidade
                break
    if not result['unidade']:
        for line in lines[:5]:
            if line.strip():
                result['unidade'] = resolver_unidade(line.strip())
                break

    mov_match = re.search(r'Movimento\s*\S*\s*(\d+)', full_text, re.IGNORECASE)
    if mov_match:
        result['movimento_num'] = mov_match.group(1)

    enc_match = re.search(r'Encerramento[:\s]+(\d{2}/\d{2}/\d{2,4})\s+[\d:]+\s*[-]\s*(\w+)', full_text, re.IGNORECASE)
    if enc_match:
        result['data_fechamento'] = enc_match.group(1)
        result['quem_fechou'] = resolver_fechador(enc_match.group(2))

    dinheiro_encerramento = 0.0
    movimento_pattern = re.compile(
        r'MOVIMENTO\s+\d+\s+([\d.,]+)\s+(Dinheiro)',
        re.IGNORECASE
    )
    for match in movimento_pattern.finditer(full_text):
        dinheiro_encerramento += normalizar_valor(match.group(1))
    result['dinheiro_encerramento'] = dinheiro_encerramento

    dinheiro_saida = 0.0
    saida_pattern = re.compile(
        r'\d{2}/\d{2}\s+[\d:]+h\s+(\S+.*?)\s+([\d.,]+)\s+Dinheiro',
        re.IGNORECASE
    )
    for match in saida_pattern.finditer(full_text):
        historico = match.group(1).strip()
        if 'MOVIMENTO' not in historico.upper():
            dinheiro_saida += normalizar_valor(match.group(2))
    result['dinheiro_saida'] = dinheiro_saida

    dep_pattern = re.compile(r'MOVIMENTO\s+\d+\s+([\d.,]+)\s+Dep', re.IGNORECASE)
    dep_total = sum(normalizar_valor(m.group(1)) for m in dep_pattern.finditer(full_text))
    if dep_total > 0:
        result['deposito_bancario'] = dep_total

    cartao_pattern = re.compile(r'MOVIMENTO\s+\d+\s+([\d.,]+)\s+Cart', re.IGNORECASE)
    cartao_total = sum(normalizar_valor(m.group(1)) for m in cartao_pattern.finditer(full_text))
    if cartao_total > 0:
        result['cartao'] = cartao_total

    fat_pattern = re.compile(r'MOVIMENTO\s+\d+\s+([\d.,]+)\s+Faturad', re.IGNORECASE)
    for m in fat_pattern.finditer(full_text):
        result['faturado'] = normalizar_valor(m.group(1))

    cort_pattern = re.compile(r'MOVIMENTO\s+\d+\s+([\d.,]+)\s+Cortesia', re.IGNORECASE)
    for m in cort_pattern.finditer(full_text):
        result['cortesia'] = normalizar_valor(m.group(1))

    uc_pattern = re.compile(r'MOVIMENTO\s+\d+\s+([\d.,]+)\s+Uso', re.IGNORECASE)
    for m in uc_pattern.finditer(full_text):
        result['uso_credito'] = normalizar_valor(m.group(1))

    return result

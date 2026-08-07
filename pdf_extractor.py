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
    'OK INN HOTEL TUBARÃO': 'Ok Inn Tubarao',
    'OK INN EXPRESS TUBARAO': 'Ok Inn Express Tubarao',
    'OK INN EXPRESS TUBARÃO': 'Ok Inn Express Tubarao',
    'OK INN HOTEL EXPRESS': 'Ok Inn Express Tubarao',
    'OK INN TUBARAO': 'Ok Inn Tubarao',
    'OK INN TUBARÃO': 'Ok Inn Tubarao',
    'OK INN EXPRESS': 'Ok Inn Express Tubarao',
    'CRICIUMA EXPRESS': 'Criciuma Express',
    'CRICIÚMA EXPRESS': 'Criciuma Express',
    'CRICIUMA CENTRO': 'Criciuma Centro',
    'CRICIÚMA CENTRO': 'Criciuma Centro',
    'FLORIPA COQUEIROS': 'Floripa Coqueiros',
    'ATLANTICO SUL': 'Atlantico Sul',
    'ATLÂNTICO SUL': 'Atlantico Sul',
    'RENASCENCA': 'Renascenca',
    'RENASCENÇA': 'Renascenca',
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
    return None


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
    unidade_encontrada = ''

    with pdfplumber.open(pdf_path) as pdf:
        first_page = pdf.pages[0]
        width = first_page.width
        height = first_page.height

        # Busca nome do hotel na metade direita do topo
        right_half = first_page.crop((width * 0.4, 0, width, height * 0.15))
        right_text = right_half.extract_text() or ''
        for line in right_text.split('\n'):
            unidade = resolver_unidade(line.strip())
            if unidade:
                unidade_encontrada = unidade
                break

        # Fallback: texto completo
        if not unidade_encontrada:
            full_page_text = first_page.extract_text() or ''
            for line in full_page_text.split('\n'):
                unidade = resolver_unidade(line.strip())
                if unidade:
                    unidade_encontrada = unidade
                    break

        result['unidade'] = unidade_encontrada

        for page in pdf.pages:
            full_text += (page.extract_text() or '') + '\n'

    # Numero do movimento
    mov_match = re.search(r'Movimento\s*\S*\s*(\d+)', full_text, re.IGNORECASE)
    if mov_match:
        result['movimento_num'] = mov_match.group(1)

    # Data e quem fechou
    enc_match = re.search(
        r'Encerramento[:\s]+(\d{2}/\d{2}/\d{2,4})\s+[\d:]+\s*[-]\s*(\w+)',
        full_text, re.IGNORECASE
    )
    if enc_match:
        result['data_fechamento'] = enc_match.group(1)
        result['quem_fechou'] = resolver_fechador(enc_match.group(2))

    # Dinheiro encerramento — apenas linhas MOVIMENTO com forma Dinheiro
    dinheiro_encerramento = 0.0
    mov_din = re.compile(
        r'MOVIMENTO\s+\d+\s+([\d.,]+)\s+Dinheiro',
        re.IGNORECASE
    )
    for match in mov_din.finditer(full_text):
        dinheiro_encerramento += normalizar_valor(match.group(1))
    result['dinheiro_encerramento'] = dinheiro_encerramento

    # Dinheiro saida — apenas linhas com formato de data/hora + historico conhecido
    # Formato: DD/MM HH:MMh AP NNN CTA NNNNN Dinheiro VALOR
    # O valor vem DEPOIS da palavra Dinheiro, precedido por espaco
    dinheiro_saida = 0.0
    saida_pat = re.compile(
        r'\d{2}/\d{2}\s+[\d:]+h\s+(?!MOVIMENTO)\S+\s+\S+\s+\S+\s+Dinheiro\s+([\d.,]+)',
        re.IGNORECASE
    )
    for match in saida_pat.finditer(full_text):
        valor = normalizar_valor(match.group(1))
        # Ignora valores muito altos que sao claramente numeros de conta
        if valor < 50000:
            dinheiro_saida += valor
    result['dinheiro_saida'] = dinheiro_saida

    # Deposito bancario
    dep_pat = re.compile(r'MOVIMENTO\s+\d+\s+([\d.,]+)\s+Dep', re.IGNORECASE)
    dep_total = sum(normalizar_valor(m.group(1)) for m in dep_pat.finditer(full_text))
    if dep_total > 0:
        result['deposito_bancario'] = dep_total

    # Cartao
    car_pat = re.compile(r'MOVIMENTO\s+\d+\s+([\d.,]+)\s+Cart', re.IGNORECASE)
    car_total = sum(normalizar_valor(m.group(1)) for m in car_pat.finditer(full_text))
    if car_total > 0:
        result['cartao'] = car_total

    # Faturado
    fat_pat = re.compile(r'MOVIMENTO\s+\d+\s+([\d.,]+)\s+Faturad', re.IGNORECASE)
    for m in fat_pat.finditer(full_text):
        result['faturado'] = normalizar_valor(m.group(1))

    # Cortesia
    cort_pat = re.compile(r'MOVIMENTO\s+\d+\s+([\d.,]+)\s+Cortesia', re.IGNORECASE)
    for m in cort_pat.finditer(full_text):
        result['cortesia'] = normalizar_valor(m.group(1))

    # Uso credito
    uc_pat = re.compile(r'MOVIMENTO\s+\d+\s+([\d.,]+)\s+Uso', re.IGNORECASE)
    for m in uc_pat.finditer(full_text):
        result['uso_credito'] = normalizar_valor(m.group(1))

    return result

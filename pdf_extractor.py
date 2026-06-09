import pdfplumber
import re

ALIAS_FECHADORES = {
    'EDEM': 'EDEMILSON',
    'EDEMILS': 'EDEMILSON',
    'EDEMILSON': 'EDEMILSON',
    'EDEMILSOM': 'EDEMILSON',
    'ALE': 'ALESSANDRA',
    'ALESSANDRA': 'ALESSANDRA',
    'ERIK': 'ERIK',
    'DEISE': 'DEISE',
    'DEIS': 'DEISE',
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
    'OK INN HOTEL CRICIUMA EXPRESS': 'Criciuma Express',
    'OK INN HOTEL CRICIÚMA EXPRESS': 'Criciuma Express',
    'OK INN HOTEL CRICIUMA CENTRO': 'Criciuma Centro',
    'OK INN HOTEL CRICIÚMA CENTRO': 'Criciuma Centro',
    'OK INN HOTEL CRICIUMA': 'Criciuma Express',
    'OK INN HOTEL CRICIÚMA': 'Criciuma Express',
    'OK INN CRICIUMA EXPRESS': 'Criciuma Express',
    'OK INN CRICIÚMA EXPRESS': 'Criciuma Express',
    'OK INN CRICIUMA CENTRO': 'Criciuma Centro',
    'OK INN CRICIÚMA CENTRO': 'Criciuma Centro',
    'CRICIUMA EXPRESS': 'Criciuma Express',
    'CRICIÚMA EXPRESS': 'Criciuma Express',
    'CRICIUMA CENTRO': 'Criciuma Centro',
    'CRICIÚMA CENTRO': 'Criciuma Centro',
    'FLORIPA COQUEIROS': 'Floripa Coqueiros',
    'ATLANTICO SUL': 'Atlantico Sul',
    'ATLÂNTICO SUL': 'Atlantico Sul',
    'RENASCENCA': 'Renascenca',
    'RENASCENÇA': 'Renascenca',
    'YOU HOTEIS INTELIGENTES 01': 'You HI 01',
    'YOU HOTEIS INTELIGENTES': 'You HI 01',
    'YOU HI 01': 'You HI 01',
    'YOU HI': 'You HI 01',
}

UNIDADES_CHEQUE_COMO_DEP = ['Atlantico Sul', 'Renascenca']
UNIDADES_SEM_COFRE = ['Atlantico Sul', 'Renascenca']


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
    for key in sorted(UNIDADE_MAP.keys(), key=len, reverse=True):
        if key in texto_upper:
            return UNIDADE_MAP[key]
    return None


def resolver_fechador(nome):
    nome_upper = nome.upper().strip()
    for key, val in ALIAS_FECHADORES.items():
        if key in nome_upper:
            return val
    return nome.strip()


def is_numero_conta(valor):
    return valor > 10000


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
        'cheque': 0.0,
        'cofre_opcional': False,
    }

    full_text = ''
    unidade_encontrada = ''

    with pdfplumber.open(pdf_path) as pdf:
        first_page = pdf.pages[0]
        width = first_page.width
        height = first_page.height

        right_half = first_page.crop((width * 0.4, 0, width, height * 0.15))
        right_text = right_half.extract_text() or ''
        for line in right_text.split('\n'):
            unidade = resolver_unidade(line.strip())
            if unidade:
                unidade_encontrada = unidade
                break

        if not unidade_encontrada:
            full_page_text = first_page.extract_text() or ''
            for line in full_page_text.split('\n'):
                unidade = resolver_unidade(line.strip())
                if unidade:
                    unidade_encontrada = unidade
                    break

        result['unidade'] = unidade_encontrada
        result['cofre_opcional'] = unidade_encontrada in UNIDADES_SEM_COFRE

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

    # Dinheiro encerramento — MOVIMENTO + valor + Dinheiro
    dinheiro_encerramento = 0.0
    mov_din = re.compile(r'MOVIMENTO\s+\d+\s+([\d.,]+)\s+Dinheiro', re.IGNORECASE)
    for match in mov_din.finditer(full_text):
        v = normalizar_valor(match.group(1))
        if not is_numero_conta(v):
            dinheiro_encerramento += v
    result['dinheiro_encerramento'] = dinheiro_encerramento

    # Dinheiro saida — linhas que NAO sao AP CTA e NAO sao MOVIMENTO
    # Formato saida real: DD/MM HH:MMh DESCRICAO VALOR Dinheiro
    # Formato antecipacao: DD/MM HH:MMh AP NNN CTA NNNNN Dinheiro VALOR
    # A diferenca: saida tem valor ANTES de Dinheiro, antecipacao tem valor DEPOIS
    # Mas ambos podem ter valor antes. O diferenciador e que antecipacao tem "AP NNN CTA"
    dinheiro_saida = 0.0
    # Padrao para saidas reais: data/hora + historico SEM "AP NNN CTA" + valor + Dinheiro
    saida_pat = re.compile(
        r'\d{2}/\d{2}\s+[\d:]+h\s+((?!AP\s+\d+\s+CTA\s+\d+)(?!MOVIMENTO).+?)\s+([\d.,]+)\s+Dinheiro',
        re.IGNORECASE
    )
    for match in saida_pat.finditer(full_text):
        historico = match.group(1).strip()
        valor = normalizar_valor(match.group(2))
        if is_numero_conta(valor):
            continue
        if valor > 0:
            dinheiro_saida += valor
    result['dinheiro_saida'] = dinheiro_saida

    # Cheque
    cheque_pat = re.compile(r'MOVIMENTO\s+\d+\s+([\d.,]+)\s+Cheque', re.IGNORECASE)
    cheque_total = sum(normalizar_valor(m.group(1)) for m in cheque_pat.finditer(full_text))

    # Deposito bancario
    dep_pat = re.compile(r'MOVIMENTO\s+\d+\s+([\d.,]+)\s+Dep', re.IGNORECASE)
    dep_total = sum(normalizar_valor(m.group(1)) for m in dep_pat.finditer(full_text))

    if unidade_encontrada in UNIDADES_CHEQUE_COMO_DEP:
        result['deposito_bancario'] = dep_total + cheque_total
        result['cheque'] = 0.0
    else:
        result['deposito_bancario'] = dep_total
        result['cheque'] = cheque_total

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

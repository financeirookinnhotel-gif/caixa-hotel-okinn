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
    'OK INN HOTEL TUBARÃO': 'Ok Inn Tubarão',
    'OK INN HOTEL TUBARAO': 'Ok Inn Tubarão',
    'OK INN EXPRESS TUBARÃO': 'Ok Inn Express Tubarão',
    'OK INN EXPRESS TUBARAO': 'Ok Inn Express Tubarão',
    'OK INN TUBARÃO': 'Ok Inn Tubarão',
    'OK INN TUBARAO': 'Ok Inn Tubarão',
    'OK INN EXPRESS': 'Ok Inn Express Tubarão',
    'CRICIÚMA EXPRESS': 'Criciúma Express',
    'CRICIUMA EXPRESS': 'Criciúma Express',
    'CRICIÚMA CENTRO': 'Criciúma Centro',
    'CRICIUMA CENTRO': 'Criciúma Centro',
    'FLORIPA COQUEIROS': 'Floripa Coqueiros',
    'ATLÂNTICO SUL': 'Atlântico Sul',
    'ATLANTICO SUL': 'Atlântico Sul',
    'RENASCENÇA': 'Renascença',
    'RENASCENCA': 'Renascença',
    'YOU HI 01': 'You HI 01',
    'YOU HI': 'You HI 01',
}


def normalizar_valor(val_str):
    """Converte string de valor brasileiro para float"""
    if not val_str:
        return 0.0
    val_str = val_str.strip().replace('R$', '').replace(' ', '')
    val_str = val_str.replace('.', '').replace(',', '.')
    try:
        return float(val_str)
    except:
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
    """
    Extrai os dados do PDF de fechamento de caixa HMAX.
    Retorna dicionário com todos os campos mapeados.
    """
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

    with pdfplumber.open(pdf_path) as pdf:
        # Pega texto das primeiras páginas
        full_text = ''
        for page in pdf.pages:
            full_text += (page.extract_text() or '') + '\n'

        lines = full_text.split('\n')

    # ── Unidade Hoteleira (item 1) ─────────────────────────────
    # Aparece como "OK INN HOTEL TUBARÃO" ou similar nas primeiras linhas
    for line in lines[:10]:
        line_stripped = line.strip()
        if line_stripped and len(line_stripped) > 5:
            unidade = resolver_unidade(line_stripped)
            if unidade != line_stripped:
                result['unidade'] = unidade
                break
    # Fallback: pega a primeira linha não vazia
    if not result['unidade']:
        for line in lines[:5]:
            if line.strip():
                result['unidade'] = resolver_unidade(line.strip())
                break

    # ── Número do movimento ────────────────────────────────────
    mov_match = re.search(r'Movimento\s*[Nº°]*\s*(\d+)', full_text, re.IGNORECASE)
    if mov_match:
        result['movimento_num'] = mov_match.group(1)

    # ── Data de fechamento e quem fechou (item 2 e 3) ──────────
    # "Encerramento: 03/02/26 03:07 - EDEM"
    enc_match = re.search(r'Encerramento[:\s]+(\d{2}/\d{2}/\d{2,4})\s+[\d:]+\s*[-–]\s*(\w+)', full_text, re.IGNORECASE)
    if enc_match:
        result['data_fechamento'] = enc_match.group(1)
        result['quem_fechou'] = resolver_fechador(enc_match.group(2))

    # ── Extrai a tabela de ANTECIPAÇÕES / movimentos (lado direito da pág 1) ──
    # Procura linhas: "Data/Hora Histórico Entrada Saída Forma"
    # Os lançamentos de MOVIMENTO são as linhas com "MOVIMENTO XXXX"
    # e a forma de pagamento indica a categoria

    # Pattern para linhas de movimento de encerramento:
    # "03/02 03:07h MOVIMENTO 2309 1500,00 Dinheiro5" (número pode estar colado)
    movimento_pattern = re.compile(
        r'MOVIMENTO\s+\d+\s+([\d.,]+)\s+(Dinheiro|Dinheiro\d|Cart[aã]o|Cart[aã]o\s*\d|Faturado\d?|Cortesia\d?|Uso\s+cr[eé]dito\d?|Dep\.\s*Banc\.\d?)',
        re.IGNORECASE
    )

    # Pattern para saídas de dinheiro que NÃO são movimento de encerramento:
    # "02/02 17:44h DEPIERI COMERCIO DE 88,00 Dinheiro"
    saida_dinheiro_pattern = re.compile(
        r'(\d{2}/\d{2})\s+[\d:]+h\s+(?!MOVIMENTO)(.+?)\s+([\d.,]+)\s+Dinheiro',
        re.IGNORECASE
    )

    dinheiro_encerramento = 0.0
    dinheiro_saida = 0.0

    for match in movimento_pattern.finditer(full_text):
        valor = normalizar_valor(match.group(1))
        forma = match.group(2).strip().lower()
        if forma.startswith('dinheiro'):
            dinheiro_encerramento += valor

    result['dinheiro_encerramento'] = dinheiro_encerramento

    # Saídas de dinheiro que não são encerramento
    for match in saida_dinheiro_pattern.finditer(full_text):
        historico = match.group(2).strip()
        # Ignora se for MOVIMENTO
        if 'MOVIMENTO' in historico.upper():
            continue
        valor = normalizar_valor(match.group(3))
        dinheiro_saida += valor

    result['dinheiro_saida'] = dinheiro_saida

    # ── Extrai da tabela principal (linha Saída) ───────────────
    # Na tabela resumo da pág 1:
    # "Saída  1588,00  17253,51  1777,00  249,00  696,00  2376,00"
    # Colunas: Dinheiro Cheque Cartão Fatura Cortesia Permuta UsoCrédito UsoCasa Outros DepBanc

    saida_line = None
    for i, line in enumerate(lines):
        if re.match(r'\s*Sa[ií]da\s', line, re.IGNORECASE):
            saida_line = line
            break

    if saida_line:
        nums = re.findall(r'[\d]+[.,]\d{2}', saida_line)
        nums = [normalizar_valor(n) for n in nums]
        # Ordem das colunas: Dinheiro, Cheque, Cartão, Fatura, Cortesia, Permuta, UsoCredito, UsoCasa, Outros(-)
        if len(nums) >= 1:
            # dinheiro já tratamos separado pelo encerramento
            pass
        if len(nums) >= 3:
            result['cartao'] = nums[2] if len(nums) > 2 else 0
        if len(nums) >= 4:
            result['faturado'] = nums[3] if len(nums) > 3 else 0
        if len(nums) >= 5:
            result['cortesia'] = nums[4] if len(nums) > 4 else 0
        if len(nums) >= 7:
            result['uso_credito'] = nums[6] if len(nums) > 6 else 0

    # ── Busca Dep. Banc. e outros nas linhas de MOVIMENTO ──────
    # "03/02 03:07h MOVIMENTO 2309 2376,00 Dep. Banc."
    dep_pattern = re.compile(
        r'MOVIMENTO\s+\d+\s+([\d.,]+)\s+Dep[\.\s]+Banc',
        re.IGNORECASE
    )
    dep_total = 0.0
    for match in dep_pattern.finditer(full_text):
        dep_total += normalizar_valor(match.group(1))
    if dep_total > 0:
        result['deposito_bancario'] = dep_total

    # Cartão do encerramento
    cartao_enc_pattern = re.compile(
        r'MOVIMENTO\s+\d+\s+([\d.,]+)\s+Cart[aã]o',
        re.IGNORECASE
    )
    cartao_total = 0.0
    for match in cartao_enc_pattern.finditer(full_text):
        cartao_total += normalizar_valor(match.group(1))
    if cartao_total > 0:
        result['cartao'] = cartao_total

    # Faturado do encerramento
    fat_pattern = re.compile(
        r'MOVIMENTO\s+\d+\s+([\d.,]+)\s+Faturad',
        re.IGNORECASE
    )
    for match in fat_pattern.finditer(full_text):
        result['faturado'] = normalizar_valor(match.group(1))

    # Cortesia do encerramento
    cort_pattern = re.compile(
        r'MOVIMENTO\s+\d+\s+([\d.,]+)\s+Cortesia',
        re.IGNORECASE
    )
    for match in cort_pattern.finditer(full_text):
        result['cortesia'] = normalizar_valor(match.group(1))

    # Uso crédito do encerramento
    uc_pattern = re.compile(
        r'MOVIMENTO\s+\d+\s+([\d.,]+)\s+Uso\s+cr[eé]d',
        re.IGNORECASE
    )
    for match in uc_pattern.finditer(full_text):
        result['uso_credito'] = normalizar_valor(match.group(1))

    return result

import pdfplumber
import re
from itertools import groupby

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


def _valor_num(texto):
    if not texto or not any(c.isdigit() for c in texto):
        return None
    return normalizar_valor(texto)


def _bounds_tabela_movimentos(words):
    """Acha os limites de coluna da tabela 'Data/Hora Historico Entrada Saida Forma'.

    O PDF do HMAX imprime essa tabela ao lado da tabela de Antecipacoes
    (adiantamentos recebidos), na mesma altura visual. O pdfplumber concatena
    as duas em uma unica linha de texto, entao so a posicao (coordenada X) das
    palavras permite separar as duas tabelas — nao da pra confiar em regex
    sobre o texto puro (ver ALIAS de 'Dinheiro' colidindo com 'Antecipacoes').
    """
    data_hora = next((w for w in words if w['text'] == 'Data/Hora'), None)
    forma = next((w for w in words if w['text'] == 'Forma'), None)
    if not (data_hora and forma):
        return None
    top_ref = round(data_hora['top'])
    def achar(opcoes):
        return next((w for w in words if w['text'] in opcoes and round(w['top']) == top_ref), None)
    historico = achar(['Histórico', 'Historico'])
    entrada = achar(['Entrada'])
    saida = achar(['Saída', 'Saida'])
    if not (historico and entrada and saida):
        return None
    return {
        'tabela_x0': data_hora['x0'] - 5,
        'historico_x0': historico['x0'] - 5,
        'entrada_x0': historico['x1'],
        'meio_entrada_saida': (entrada['x1'] + saida['x0']) / 2,
        'meio_saida_forma': (saida['x1'] + forma['x0']) / 2,
        'forma_x0': forma['x0'] - 3,
    }


def _dinheiro_saida_posicional(pdf):
    """Soma os valores da coluna 'Saida' com forma 'Dinheiro' na tabela de
    movimentos, excluindo a(s) linha(s) de MOVIMENTO (essas ja sao contadas
    em dinheiro_encerramento, item 5)."""
    bounds = None
    for page in pdf.pages:
        bounds = _bounds_tabela_movimentos(page.extract_words())
        if bounds:
            break
    if not bounds:
        return None

    total = 0.0
    for page in pdf.pages:
        palavras = [w for w in page.extract_words() if w['x0'] >= bounds['tabela_x0']]
        palavras.sort(key=lambda w: (round(w['top']), w['x0']))
        for _, grupo in groupby(palavras, key=lambda w: round(w['top'])):
            grupo = list(grupo)
            textos = [w['text'] for w in grupo]
            if 'Data/Hora' in textos or 'Forma' in textos:
                continue
            historico = ' '.join(
                w['text'] for w in grupo
                if bounds['historico_x0'] <= w['x0'] < bounds['entrada_x0']
            )
            forma = ' '.join(
                w['text'] for w in grupo if w['x0'] >= bounds['forma_x0']
            )
            if 'Dinheiro' not in forma or 'MOVIMENTO' in historico.upper():
                continue
            saida_toks = [
                w for w in grupo
                if bounds['meio_entrada_saida'] <= w['x0'] < bounds['meio_saida_forma']
            ]
            for w in saida_toks:
                valor = _valor_num(w['text'])
                if valor:
                    total += valor
    return total


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

        dinheiro_saida_posicional = _dinheiro_saida_posicional(pdf)

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

    # Dinheiro saida (item 4 - saida nao relacionada ao encerramento).
    # Calculado por posicao (coluna 'Saida' da tabela de movimentos), pois a
    # tabela de Antecipacoes fica ao lado e tem o mesmo formato textual
    # "data hora ... Dinheiro valor" — so a posicao X distingue as duas.
    result['dinheiro_saida'] = dinheiro_saida_posicional or 0.0

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

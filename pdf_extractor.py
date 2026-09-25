import logging
import pdfplumber
import re
from itertools import groupby

# Alguns PDFs do HITS tem fontes com descritor malformado (FontBBox
# invalido). O pdfminer (usado pelo pdfplumber por baixo dos panos) loga
# um aviso para cada ocorrencia — em paginas com muito texto isso emite
# milhares de linhas e chega a dobrar o tempo de extract_text(). Como o
# fallback do pdfminer ja lida com isso sem quebrar a extracao, so
# silenciamos o log (nao muda o resultado, so a performance).
logging.getLogger('pdfminer').setLevel(logging.ERROR)

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
    'OK INN HOTEL TUBARAO EXPRESS': 'Ok Inn Express Tubarao',
    'OK INN HOTEL TUBARÃO EXPRESS': 'Ok Inn Express Tubarao',
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
    'OK INN HOTEL CRICIUMA CENTRO': 'Criciuma Centro',
    'OK INN HOTEL CRICIÚMA CENTRO': 'Criciuma Centro',
    'OK INN HOTEL CRICIUMA EXPRESS': 'Criciuma Express',
    'OK INN HOTEL CRICIÚMA EXPRESS': 'Criciuma Express',
    'OK INN HOTEL CRICIUMA': 'Criciuma Express',
    'OK INN HOTEL CRICIÚMA': 'Criciuma Express',
    'OK INN CRICIUMA': 'Criciuma Express',
    'OK INN CRICIÚMA': 'Criciuma Express',
    'FLORIPA COQUEIROS': 'Floripa Coqueiros',
    'ATLANTICO SUL': 'Atlantico Sul',
    'ATLÂNTICO SUL': 'Atlantico Sul',
    'RENASCENCA': 'Renascenca',
    'RENASCENÇA': 'Renascenca',
    'YOU HI 01': 'You HI 01',
    'YOU HI': 'You HI 01',
    'YOU HOTEIS INTELIGENTES 01': 'You HI 01',
    'YOU HOTÉIS INTELIGENTES 01': 'You HI 01',
    'YOU HOTEIS INTELIGENTES': 'You HI 01',
    'YOU HOTÉIS INTELIGENTES': 'You HI 01',
}


def normalizar_valor(val_str):
    if not val_str:
        return 0.0
    val_str = val_str.strip().replace('R$', '').replace('$', '').replace(' ', '')
    val_str = val_str.replace('.', '').replace(',', '.')
    try:
        return float(val_str)
    except Exception:
        return 0.0


def resolver_unidade(texto):
    texto_upper = texto.upper().strip()
    # Prefere a chave mais especifica (mais longa) que casar, para que um
    # nome generico (ex.: "OK INN HOTEL TUBARAO") nao "roube" o casamento
    # de um nome mais completo que tambem contem esse prefixo (ex.: "OK INN
    # HOTEL TUBARAO EXPRESS").
    melhor_chave = None
    melhor_valor = None
    for key, val in UNIDADE_MAP.items():
        if key in texto_upper and (melhor_chave is None or len(key) > len(melhor_chave)):
            melhor_chave = key
            melhor_valor = val
    return melhor_valor


def resolver_fechador(nome):
    nome_upper = nome.upper().strip()
    for key, val in ALIAS_FECHADORES.items():
        if key in nome_upper:
            return val
    return nome.strip()


# Unidades sem cofre com dinheiro fixo — fecham so com recibo, entao o
# envio ao cofre e opcional (o Diretor pode pular direto para concluido).
UNIDADES_SEM_COFRE_FIXO = {'Atlantico Sul', 'Renascenca'}


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
        'cheque': 0.0,
        'cofre_opcional': False,
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
        result['cofre_opcional'] = unidade_encontrada in UNIDADES_SEM_COFRE_FIXO

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

    # Cheque — soma no deposito bancario (cheque depositado tambem e
    # deposito bancario) e guarda a parte separada em 'cheque' so para
    # exibir o rotulo "+ Cheque" no relatorio.
    cheque_pat = re.compile(r'MOVIMENTO\s+\d+\s+([\d.,]+)\s+Cheque', re.IGNORECASE)
    cheque_total = sum(normalizar_valor(m.group(1)) for m in cheque_pat.finditer(full_text))
    if cheque_total > 0:
        result['cheque'] = cheque_total
        result['deposito_bancario'] += cheque_total

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


# ─── Extrator do sistema HITS (novo PMS, substituindo o HMAX aos poucos) ──

def _parse_resumo_caixa_hits(tabela):
    """Le a tabela 'Resumo do caixa' do HITS e retorna {tipo_pagamento: total}.

    Cada linha da tabela tem o tipo de pagamento na 1a celula (pode vir
    quebrado em varias linhas dentro da mesma celula, ex.: 'STONE\\nVISA\\n
    CREDITO') e o valor "Total" na ultima celula. Usa extract_tables() em
    vez de regex sobre o texto porque o pdfplumber ja separa as colunas
    corretamente aqui (ao contrario do HMAX, que exige truque de posicao).
    """
    totais = {}
    dentro_da_secao = False
    for row in tabela:
        label_cell = row[0] or ''
        if 'Tipo de Pagto' in label_cell:
            dentro_da_secao = True
            continue
        if not dentro_da_secao:
            continue
        label = ' '.join(label_cell.split()).upper()
        if not label or label in ('SUB TOTAL', 'TOTAL DO CAIXA'):
            break
        total_cell = None
        for cell in reversed(row):
            if cell and any(c.isdigit() for c in cell):
                total_cell = cell
                break
        if total_cell:
            totais[label] = totais.get(label, 0.0) + normalizar_valor(total_cell)
    return totais


CAIXA_HITS_HEADER_RE = re.compile(
    r'#(\d+)\s+\S+\s+(\d{2}/\d{2}/\d{4})\s+\d{2}:\d{2}\s+(.+?)\s+'
    r'(\d{2}/\d{2}/\d{4})\s+\d{2}:\d{2}\s+(.+?)\s+\$([\d.,]+)',
    re.IGNORECASE
)


TRANSACAO_HITS_RE = re.compile(r'(?=#\d+\s*-\s*)')
TRANSACAO_HITS_TIPO_RE = re.compile(r'#(\d+)\s*-\s*(.+?)\s*-\s*')


def extract_transacoes_cartao_hits(pdf_path):
    """Abre o PDF e extrai as transacoes de cartao (uso avulso/externo —
    dentro de extract_caixa_data_hits usa-se _parse_transacoes_cartao_hits
    direto, reaproveitando o texto ja extraido, para nao abrir o PDF
    duas vezes)."""
    full_text = ''
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            full_text += (page.extract_text() or '') + '\n'
    return _parse_transacoes_cartao_hits(full_text)


def _parse_transacoes_cartao_hits(full_text):
    """Extrai as transacoes individuais de cartao (Stone Mastercard/Visa
    Credito/Debito) do log detalhado do fechamento do HITS, para cruzar
    com a planilha de vendas da Stone pelo STONE ID (campo 'aut.:' aqui).

    Fica de fora de proposito (o usuario decidiu dar o aceite manual):
    Stone Pix, Dinheiro, Transferencia Bancaria, Virada de Sistema,
    Faturado, Pix CNPJ — nenhuma dessas tem 'aut.:'/'doc.:' no PDF.
    """
    transacoes = []
    for parte in TRANSACAO_HITS_RE.split(full_text):
        m_tipo = TRANSACAO_HITS_TIPO_RE.match(parte)
        if not m_tipo:
            continue
        num, tipo = m_tipo.group(1), m_tipo.group(2).strip()
        tipo_upper = tipo.upper()
        if 'STONE' not in tipo_upper or 'PIX' in tipo_upper:
            continue
        m_aut = re.search(r'aut\.:\s*(\S+)', parte)
        valores = re.findall(r'\$([\d.,]+)', parte)
        if not (m_aut and valores):
            continue
        transacoes.append({
            'num_transacao': num,
            'tipo': tipo,
            'stone_id': m_aut.group(1),
            'valor': normalizar_valor(valores[-1]),
        })
    return transacoes


def extract_caixa_data_hits(pdf_path):
    result = {
        'unidade': '',
        'data_fechamento': '',
        'quem_fechou': '',
        'movimento_num': '',
        'dinheiro_encerramento': 0.0,
        'faturado': 0.0,
        'hits_stone_total': 0.0,
        'hits_transferencia_bancaria': 0.0,
        'hits_pix_cnpj': 0.0,
        'hits_virada_sistema': 0.0,
        'total_caixa': 0.0,
        'cofre_opcional': False,
        'transacoes_cartao': [],
    }

    with pdfplumber.open(pdf_path) as pdf:
        first_page = pdf.pages[0]
        full_text = first_page.extract_text() or ''
        lines = [l for l in full_text.split('\n') if l.strip()]

        if lines:
            result['unidade'] = resolver_unidade(lines[0]) or ''
        result['cofre_opcional'] = result['unidade'] in UNIDADES_SEM_COFRE_FIXO

        header_match = CAIXA_HITS_HEADER_RE.search(full_text)
        if header_match:
            result['movimento_num'] = header_match.group(1)
            result['data_fechamento'] = header_match.group(4)
            result['quem_fechou'] = resolver_fechador(header_match.group(5))
            result['total_caixa'] = normalizar_valor(header_match.group(6))

        tabelas = first_page.extract_tables()
        totais = {}
        for tabela in tabelas:
            totais.update(_parse_resumo_caixa_hits(tabela))

        # Reaproveita as paginas ja abertas (nao abre o PDF de novo) para
        # pegar o log detalhado (onde ficam as transacoes de cartao) —
        # em Render isso evita estourar o timeout do gunicorn processando
        # o mesmo PDF duas vezes.
        texto_todas_paginas = full_text
        for page in pdf.pages[1:]:
            texto_todas_paginas += '\n' + (page.extract_text() or '')

    # O "Documento avulso" da linha DINHEIRO no resumo inclui o fundo de
    # caixa (dinheiro que ja estava na gaveta, nao e venda nova) somado ao
    # total. O fundo de caixa aparece detalhado na secao "Documentos" do
    # log, ex.: "DINHEIRO - fundo de caixa $424,00" — subtrai isso do
    # Dinheiro para nao inflar o valor que vai para o cofre.
    fundo_caixa_re = re.compile(r'DINHEIRO\s*-\s*fundo de caixa\s+\$([\d.,]+)', re.IGNORECASE)
    fundo_caixa_total = sum(
        normalizar_valor(m.group(1)) for m in fundo_caixa_re.finditer(texto_todas_paginas)
    )
    result['dinheiro_encerramento'] = totais.get('DINHEIRO', 0.0) - fundo_caixa_total
    result['faturado'] = totais.get('FATURADO', 0.0)
    result['hits_transferencia_bancaria'] = totais.get('TRANSFERENCIA BANCARIA', 0.0)
    result['hits_pix_cnpj'] = totais.get('PIX CNPJ', 0.0)
    result['hits_virada_sistema'] = totais.get('VIRADA DE SISTEMA', 0.0)
    result['hits_stone_total'] = sum(v for k, v in totais.items() if 'STONE' in k)
    result['transacoes_cartao'] = _parse_transacoes_cartao_hits(texto_todas_paginas)

    return result

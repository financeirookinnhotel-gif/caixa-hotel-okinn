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

    with pdfplumber.open(pdf_path) as pd

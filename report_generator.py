from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from datetime import datetime
import os


def check_str(val):
    return '✓' if val else '✗'


def fmt_valor(val):
    if val is None:
        return 'R$ 0,00'
    return f'R$ {val:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')


def gerar_pdf_relatorio(fc, financeiro_user, diretor_user):
    os.makedirs('relatorios', exist_ok=True)
    path = f'relatorios/relatorio_fc_{fc.id}_{datetime.now().strftime("%Y%m%d%H%M%S")}.pdf'

    doc = SimpleDocTemplate(path, pagesize=A4,
                            topMargin=1.5*cm, bottomMargin=1.5*cm,
                            leftMargin=2*cm, rightMargin=2*cm)

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('Title', parent=styles['Title'],
                                  fontSize=16, textColor=colors.HexColor('#1a3a5c'),
                                  spaceAfter=6)
    sub_style = ParagraphStyle('Sub', parent=styles['Normal'],
                                fontSize=10, textColor=colors.grey, spaceAfter=12)
    section_style = ParagraphStyle('Section', parent=styles['Normal'],
                                    fontSize=12, textColor=colors.HexColor('#1a3a5c'),
                                    fontName='Helvetica-Bold', spaceBefore=12, spaceAfter=6)
    normal = styles['Normal']

    story = []

    # Cabeçalho
    story.append(Paragraph('RELATÓRIO DE FECHAMENTO DE CAIXA', title_style))
    story.append(Paragraph(f'{fc.unidade} | Movimento Nº {fc.movimento_num}', sub_style))
    story.append(HRFlowable(width='100%', thickness=2, color=colors.HexColor('#1a3a5c')))
    story.append(Spacer(1, 0.3*cm))

    # Dados gerais
    story.append(Paragraph('DADOS DO FECHAMENTO', section_style))
    dados = [
        ['Unidade', fc.unidade],
        ['Data de Fechamento', fc.data_fechamento],
        ['Fechado por', fc.quem_fechou],
        ['Movimento Nº', fc.movimento_num],
        ['Status', fc.status_label()],
        ['Data de Upload', fc.created_at.strftime('%d/%m/%Y %H:%M') if fc.created_at else '-'],
    ]
    t = Table(dados, colWidths=[5*cm, 11*cm])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e8f0fe')),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(t)
    story.append(Spacer(1, 0.4*cm))

    # Valores
    story.append(Paragraph('VALORES DO CAIXA', section_style))
    valores_data = [
        ['Item', 'Valor', 'Financeiro', 'Diretor'],
        ['Dinheiro (Saída)', fmt_valor(fc.dinheiro_saida),
         check_str(fc.financeiro_check_dinheiro), check_str(fc.diretor_check_dinheiro)],
        ['Dinheiro (Encerramento)', fmt_valor(fc.dinheiro_encerramento),
         check_str(fc.financeiro_check_dinheiro), check_str(fc.diretor_check_dinheiro)],
        ['Cartão', fmt_valor(fc.cartao),
         check_str(fc.financeiro_check_cartao), check_str(fc.diretor_check_cartao)],
        ['Faturado', fmt_valor(fc.faturado),
         check_str(fc.financeiro_check_faturado), check_str(fc.diretor_check_faturado)],
        ['Uso de Crédito', fmt_valor(fc.uso_credito),
         check_str(fc.financeiro_check_uso_credito), check_str(fc.diretor_check_uso_credito)],
        ['Depósito Bancário', fmt_valor(fc.deposito_bancario),
         check_str(fc.financeiro_check_deposito), check_str(fc.diretor_check_deposito)],
        ['Cortesia', fmt_valor(fc.cortesia),
         check_str(fc.financeiro_check_cortesia), check_str(fc.diretor_check_cortesia)],
    ]
    if fc.tem_vendas_online:
        valores_data.append([
            f'Vendas Online ({fc.vendas_online_obs or ""})',
            fmt_valor(fc.vendas_online),
            check_str(fc.financeiro_check_vendas_online),
            check_str(fc.diretor_check_vendas_online),
        ])

    t2 = Table(valores_data, colWidths=[6*cm, 4*cm, 3*cm, 3*cm])
    t2.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a3a5c')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
        ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(t2)
    story.append(Spacer(1, 0.4*cm))

    # Conferências
    story.append(Paragraph('CONFERÊNCIAS', section_style))
    conf_data = [['', 'Usuário', 'Data/Hora', 'Observações']]

    fin_name = financeiro_user.name if financeiro_user else '-'
    fin_at = fc.financeiro_at.strftime('%d/%m/%Y %H:%M') if fc.financeiro_at else '-'
    conf_data.append(['FINANCEIRO', fin_name, fin_at, fc.financeiro_obs or '-'])

    dir_name = diretor_user.name if diretor_user else '-'
    dir_at = fc.diretor_at.strftime('%d/%m/%Y %H:%M') if fc.diretor_at else '-'
    conf_data.append(['DIRETOR', dir_name, dir_at, fc.diretor_obs or '-'])

    cofre_at = fc.cofre_at.strftime('%d/%m/%Y %H:%M') if fc.cofre_at else '-'
    conf_data.append(['COFRE', dir_name, cofre_at, fc.cofre_obs or '-'])

    t3 = Table(conf_data, colWidths=[3.5*cm, 3.5*cm, 4*cm, 5*cm])
    t3.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a3a5c')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(t3)

    # Rodapé
    story.append(Spacer(1, 1*cm))
    story.append(HRFlowable(width='100%', thickness=1, color=colors.lightgrey))
    story.append(Spacer(1, 0.2*cm))
    story.append(Paragraph(
        f'Relatório gerado em {datetime.now().strftime("%d/%m/%Y às %H:%M")} | Sistema de Fechamento de Caixa OK INN',
        ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8,
                       textColor=colors.grey, alignment=TA_CENTER)
    ))

    doc.build(story)
    return path

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable
from reportlab.lib.enums import TA_CENTER
from datetime import datetime
import os


def fmt_valor(val):
    if val is None:
        return 'R$ 0,00'
    return 'R$ {:,.2f}'.format(val).replace(',', 'X').replace('.', ',').replace('X', '.')


def gerar_pdf_relatorio(fc, financeiro_user, diretor_user):
    os.makedirs('relatorios', exist_ok=True)
    path = 'relatorios/relatorio_fc_' + str(fc.id) + '_' + datetime.now().strftime('%Y%m%d%H%M%S') + '.pdf'

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
    footer_style = ParagraphStyle('Footer', parent=styles['Normal'],
                                  fontSize=8, textColor=colors.grey, alignment=TA_CENTER)

    story = []

    story.append(Paragraph('RELATORIO DE FECHAMENTO DE CAIXA', title_style))
    story.append(Paragraph(fc.unidade + ' | Movimento No ' + str(fc.movimento_num), sub_style))
    story.append(HRFlowable(width='100%', thickness=2, color=colors.HexColor('#1a3a5c')))
    story.append(Spacer(1, 0.3*cm))

    story.append(Paragraph('DADOS DO FECHAMENTO', section_style))
    dados = [
        ['Unidade', fc.unidade],
        ['Data de Fechamento', fc.data_fechamento],
        ['Fechado por', fc.quem_fechou],
        ['Movimento No', str(fc.movimento_num)],
        ['Status', fc.status_label()],
        ['Upload em', fc.created_at.strftime('%d/%m/%Y %H:%M') if fc.created_at else '-'],
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

    story.append(Paragraph('VALORES DO CAIXA', section_style))
    fin_din = 'SIM' if fc.financeiro_check_dinheiro else 'NAO'
    dir_din = 'SIM' if fc.diretor_check_dinheiro else 'NAO'
    fin_car = 'SIM' if fc.financeiro_check_cartao else 'NAO'
    dir_car = 'SIM' if fc.diretor_check_cartao else 'NAO'
    fin_fat = 'SIM' if fc.financeiro_check_faturado else 'NAO'
    dir_fat = 'SIM' if fc.diretor_check_faturado else 'NAO'
    fin_uc = 'SIM' if fc.financeiro_check_uso_credito else 'NAO'
    dir_uc = 'SIM' if fc.diretor_check_uso_credito else 'NAO'
    fin_dep = 'SIM' if fc.financeiro_check_deposito else 'NAO'
    dir_dep = 'SIM' if fc.diretor_check_deposito else 'NAO'
    fin_cort = 'SIM' if fc.financeiro_check_cortesia else 'NAO'
    dir_cort = 'SIM' if fc.diretor_check_cortesia else 'NAO'

    valores_data = [
        ['Item', 'Valor', 'Financeiro', 'Diretor'],
        ['4 - Dinheiro Saida', fmt_valor(fc.dinheiro_saida), '-', '-'],
        ['5 - Dinheiro Encerramento', fmt_valor(fc.dinheiro_encerramento), fin_din, dir_din],
        ['9 - Cartao', fmt_valor(fc.cartao), fin_car, dir_car],
        ['6 - Faturado', fmt_valor(fc.faturado), fin_fat, dir_fat],
        ['7 - Uso de Credito', fmt_valor(fc.uso_credito), fin_uc, dir_uc],
        ['8 - Deposito Bancario', fmt_valor(fc.deposito_bancario), fin_dep, dir_dep],
        ['10 - Cortesia', fmt_valor(fc.cortesia), fin_cort, dir_cort],
    ]
    if fc.tem_vendas_online:
        fin_vo = 'SIM' if fc.financeiro_check_vendas_online else 'NAO'
        dir_vo = 'SIM' if fc.diretor_check_vendas_online else 'NAO'
        valores_data.append(['Vendas Online', fmt_valor(fc.vendas_online), fin_vo, dir_vo])

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

    story.append(Paragraph('CONFERENCIAS E APROVACOES', section_style))
    fin_name = financeiro_user.name if financeiro_user else '-'
    fin_at = fc.financeiro_at.strftime('%d/%m/%Y %H:%M') if fc.financeiro_at else '-'
    dir_name = diretor_user.name if diretor_user else '-'
    dir_at = fc.diretor_at.strftime('%d/%m/%Y %H:%M') if fc.diretor_at else '-'
    cofre_at = fc.cofre_at.strftime('%d/%m/%Y %H:%M') if fc.cofre_at else '-'

    conf_data = [
        ['Etapa', 'Responsavel', 'Data/Hora', 'Observacoes'],
        ['FINANCEIRO', fin_name, fin_at, fc.financeiro_obs or '-'],
        ['DIRETOR', dir_name, dir_at, fc.diretor_obs or '-'],
        ['COFRE', dir_name, cofre_at, fc.cofre_obs or '-'],
    ]

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

    story.append(Spacer(1, 1*cm))
    story.append(HRFlowable(width='100%', thickness=1, color=colors.lightgrey))
    story.append(Spacer(1, 0.2*cm))
    story.append(Paragraph(
        'Relatorio gerado em ' + datetime.now().strftime('%d/%m/%Y as %H:%M') + ' | Sistema OK INN Leve Hoteis',
        footer_style
    ))

    doc.build(story)
    return path

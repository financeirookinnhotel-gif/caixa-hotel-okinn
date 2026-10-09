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


def gerar_pdf_relatorio(fc, financeiro_user, diretor_user, cruzamento=None):
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
        ['Sistema', (fc.sistema_pms or 'hmax').upper()],
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
    if fc.sistema_pms == 'hits':
        fin_din = 'SIM' if fc.financeiro_check_dinheiro else 'NAO'
        valores_data = [
            ['Item', 'Valor', 'Financeiro'],
            ['Dinheiro (coluna Lancamento, sem fundo de caixa)', fmt_valor(fc.dinheiro_encerramento), fin_din],
            ['Stone (cartoes + Stone Pix)', fmt_valor(fc.hits_stone_total), '-'],
            ['Faturado', fmt_valor(fc.faturado), '-'],
            ['Transferencia Bancaria', fmt_valor(fc.hits_transferencia_bancaria), '-'],
            ['Pix CNPJ', fmt_valor(fc.hits_pix_cnpj), '-'],
            ['Virada de Sistema', fmt_valor(fc.hits_virada_sistema), '-'],
            ['Total do Caixa', fmt_valor(fc.hits_total_caixa), '-'],
        ]
        t2 = Table(valores_data, colWidths=[9*cm, 4*cm, 3*cm])
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
        story.append(Paragraph('HITS: somente o Dinheiro e conferido pelo Financeiro e nao vai ao cofre.',
                               sub_style))
        if cruzamento is not None:
            n_ok = len([c for c in cruzamento if c['status'] == 'ok'])
            story.append(Paragraph('CRUZAMENTO DE CARTOES (STONE)', section_style))
            story.append(Paragraph(str(n_ok) + ' de ' + str(len(cruzamento)) +
                                   ' vendas conferidas (STONE ID encontrado e valor igual ao da Stone)',
                                   sub_style))
            rotulo = {'ok': 'Conferido', 'divergente': 'Valor diferente', 'nao_encontrado': 'Nao encontrado'}
            cz = [['Tipo', 'Stone ID', 'Valor', 'Status']]
            for c in cruzamento:
                tr = c['transacao']
                st = rotulo.get(c['status'], c['status'])
                if c['status'] == 'divergente' and c['stone'] is not None:
                    st += ' (Stone: ' + fmt_valor(c['stone'].valor_bruto) + ')'
                cz.append([tr.tipo, tr.stone_id, fmt_valor(tr.valor), st])
            tc = Table(cz, colWidths=[4.8*cm, 3.6*cm, 2.4*cm, 5.2*cm], repeatRows=1)
            tc.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a3a5c')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
                ('ALIGN', (2, 0), (2, -1), 'RIGHT'),
                ('PADDING', (0, 0), (-1, -1), 4),
            ]))
            story.append(tc)
    else:
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
    ]
    if fc.sistema_pms != 'hits':
        conf_data.append(['DIRETOR', dir_name, dir_at, fc.diretor_obs or '-'])
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

    story.append(Spacer(1, 1*cm))
    story.append(HRFlowable(width='100%', thickness=1, color=colors.lightgrey))
    story.append(Spacer(1, 0.2*cm))
    story.append(Paragraph(
        'Relatorio gerado em ' + datetime.now().strftime('%d/%m/%Y as %H:%M') + ' | Sistema OK INN Leve Hoteis',
        footer_style
    ))

    doc.build(story)
    return path


def gerar_pdf_conferencia(fc, financeiro_user, cruzamento=None):
    """PDF so com a conferencia do Financeiro (itens conferidos, observacoes e,
    para HITS, o cruzamento de cartoes com a Stone). Retorna um BytesIO."""
    from io import BytesIO
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=1.5*cm, bottomMargin=1.5*cm,
                            leftMargin=2*cm, rightMargin=2*cm)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('Title', parent=styles['Title'], fontSize=16,
                                 textColor=colors.HexColor('#1a3a5c'), spaceAfter=6)
    sub_style = ParagraphStyle('Sub', parent=styles['Normal'], fontSize=10,
                               textColor=colors.grey, spaceAfter=8)
    section_style = ParagraphStyle('Section', parent=styles['Normal'], fontSize=12,
                                   textColor=colors.HexColor('#1a3a5c'), fontName='Helvetica-Bold',
                                   spaceBefore=12, spaceAfter=6)
    footer_style = ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8,
                                  textColor=colors.grey, alignment=TA_CENTER)
    verde = colors.HexColor('#198754')
    vermelho = colors.HexColor('#dc3545')
    hits = fc.sistema_pms == 'hits'
    conferido = bool(fc.financeiro_at)

    story = [Paragraph('CONFERENCIA DO FINANCEIRO', title_style),
             Paragraph(fc.unidade + ' | Movimento No ' + str(fc.movimento_num) + ' | ' +
                       (fc.sistema_pms or 'hmax').upper(), sub_style),
             HRFlowable(width='100%', thickness=2, color=colors.HexColor('#1a3a5c')),
             Spacer(1, 0.3*cm)]

    fin_name = financeiro_user.name if financeiro_user else '-'
    fin_at = fc.financeiro_at.strftime('%d/%m/%Y %H:%M') if fc.financeiro_at else '-'
    dados = [
        ['Unidade', fc.unidade],
        ['Data de Fechamento', fc.data_fechamento],
        ['Fechado por', fc.quem_fechou or '-'],
        ['Conferido por', fin_name if conferido else 'PENDENTE - ainda nao conferido'],
        ['Conferido em', fin_at],
    ]
    t = Table(dados, colWidths=[5*cm, 11*cm])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e8f0fe')),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(t)

    story.append(Paragraph('ITENS CONFERIDOS', section_style))
    if hits:
        itens = [('Dinheiro (coluna Lancamento, sem fundo de caixa)', fc.dinheiro_encerramento,
                  fc.financeiro_check_dinheiro)]
    else:
        itens = [
            ('4 - Dinheiro Saida', fc.dinheiro_saida, fc.financeiro_check_dinheiro),
            ('5 - Dinheiro Encerramento', fc.dinheiro_encerramento, fc.financeiro_check_dinheiro),
            ('9 - Cartao', fc.cartao, fc.financeiro_check_cartao),
            ('6 - Faturado', fc.faturado, fc.financeiro_check_faturado),
            ('7 - Uso de Credito', fc.uso_credito, fc.financeiro_check_uso_credito),
            ('8 - Deposito Bancario', fc.deposito_bancario, fc.financeiro_check_deposito),
            ('10 - Cortesia', fc.cortesia, fc.financeiro_check_cortesia),
        ]
    if fc.tem_vendas_online:
        itens.append(('Vendas Online', fc.vendas_online, fc.financeiro_check_vendas_online))
    linhas = [['Item', 'Valor', 'Conferencia']]
    estilos = [
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a3a5c')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('ALIGN', (2, 0), (2, -1), 'CENTER'),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]
    for n, (label, val, ok) in enumerate(itens, start=1):
        if not conferido:
            txt, cor = 'PENDENTE', colors.grey
        elif ok:
            txt, cor = 'CONFERIDO', verde
        else:
            txt, cor = 'SEM CHECK', vermelho
        linhas.append([label, fmt_valor(val), txt])
        estilos.append(('TEXTCOLOR', (2, n), (2, n), cor))
        estilos.append(('FONTNAME', (2, n), (2, n), 'Helvetica-Bold'))
    tab = Table(linhas, colWidths=[9*cm, 4*cm, 3*cm])
    tab.setStyle(TableStyle(estilos))
    story.append(tab)

    if hits:
        story.append(Paragraph('Stone, Faturado, Transferencia Bancaria, Pix CNPJ e Virada de Sistema '
                               'nao entram na conferencia (informativo).', sub_style))
        info = [['Informativo (HITS)', 'Valor'],
                ['Stone (cartoes + Stone Pix)', fmt_valor(fc.hits_stone_total)],
                ['Faturado', fmt_valor(fc.faturado)],
                ['Transferencia Bancaria', fmt_valor(fc.hits_transferencia_bancaria)],
                ['Pix CNPJ', fmt_valor(fc.hits_pix_cnpj)],
                ['Virada de Sistema', fmt_valor(fc.hits_virada_sistema)],
                ['Total do Caixa', fmt_valor(fc.hits_total_caixa)]]
        ti = Table(info, colWidths=[9*cm, 4*cm])
        ti.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e8f0fe')),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('PADDING', (0, 0), (-1, -1), 4),
        ]))
        story.append(ti)

    if cruzamento is not None:
        n_ok = len([c for c in cruzamento if c['status'] == 'ok'])
        story.append(Paragraph('CRUZAMENTO DE CARTOES (STONE)', section_style))
        story.append(Paragraph(str(n_ok) + ' de ' + str(len(cruzamento)) +
                               ' vendas conferidas (STONE ID encontrado e valor igual ao da Stone)',
                               sub_style))
        rotulo = {'ok': 'Conferido', 'divergente': 'Valor diferente', 'nao_encontrado': 'Nao encontrado'}
        cz = [['Tipo', 'Stone ID', 'Valor', 'Status']]
        est = [
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a3a5c')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ('ALIGN', (2, 0), (2, -1), 'RIGHT'),
            ('PADDING', (0, 0), (-1, -1), 4),
        ]
        for n, c in enumerate(cruzamento, start=1):
            tr = c['transacao']
            st = rotulo.get(c['status'], c['status'])
            if c['status'] == 'divergente' and c['stone'] is not None:
                st += ' (Stone: ' + fmt_valor(c['stone'].valor_bruto) + ')'
            cz.append([tr.tipo, tr.stone_id, fmt_valor(tr.valor), st])
            est.append(('TEXTCOLOR', (3, n), (3, n), verde if c['status'] == 'ok' else vermelho))
        tc = Table(cz, colWidths=[4.8*cm, 3.6*cm, 2.4*cm, 5.2*cm], repeatRows=1)
        tc.setStyle(TableStyle(est))
        story.append(tc)

    story.append(Paragraph('OBSERVACOES', section_style))
    story.append(Paragraph(fc.financeiro_obs or 'Sem observacoes.', styles['Normal']))

    story.append(Spacer(1, 1*cm))
    story.append(HRFlowable(width='100%', thickness=1, color=colors.lightgrey))
    story.append(Spacer(1, 0.2*cm))
    story.append(Paragraph('Gerado em ' + datetime.now().strftime('%d/%m/%Y as %H:%M') +
                           ' | Sistema OK INN Leve Hoteis', footer_style))
    doc.build(story)
    buffer.seek(0)
    return buffer

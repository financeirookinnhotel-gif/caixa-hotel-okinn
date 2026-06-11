from flask import Flask, render_template, redirect, url_for, flash, request, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
import os
from pdf_extractor import extract_caixa_data

app = Flask(__name__)
database_url = os.environ.get('DATABASE_URL', 'sqlite:///caixa_hotel.db')
if database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql://', 1)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_pre_ping': True,
    'pool_recycle': 300,
}
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Faca login para acessar o sistema.'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs('relatorios', exist_ok=True)

UNIDADES = [
    'Ok Inn Tubarao',
    'Ok Inn Express Tubarao',
    'Criciuma Express',
    'Criciuma Centro',
    'Floripa Coqueiros',
    'Atlantico Sul',
    'Renascenca',
    'You HI 01',
]
UNIDADES_ATIVAS = [u for u in UNIDADES if u != 'Floripa Coqueiros']
UNIDADES_COFRE = UNIDADES + ['Leve']
ROLES = ['financeiro', 'diretor', 'admin']


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    active = db.Column(db.Boolean, default=True)
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class FechamentoCaixa(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    unidade = db.Column(db.String(120), nullable=False)
    data_fechamento = db.Column(db.String(20), nullable=False)
    quem_fechou = db.Column(db.String(80), nullable=False)
    movimento_num = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    pdf_path = db.Column(db.String(256))
    tem_vendas_online = db.Column(db.Boolean, default=False)
    dinheiro_saida = db.Column(db.Float, default=0.0)
    dinheiro_encerramento = db.Column(db.Float, default=0.0)
    faturado = db.Column(db.Float, default=0.0)
    uso_credito = db.Column(db.Float, default=0.0)
    deposito_bancario = db.Column(db.Float, default=0.0)
    cartao = db.Column(db.Float, default=0.0)
    cortesia = db.Column(db.Float, default=0.0)
    cheque = db.Column(db.Float, default=0.0)
    vendas_online = db.Column(db.Float, default=0.0)
    vendas_online_obs = db.Column(db.String(256))
    cofre_opcional = db.Column(db.Boolean, default=False)
    financeiro_check_dinheiro = db.Column(db.Boolean, default=False)
    financeiro_check_cartao = db.Column(db.Boolean, default=False)
    financeiro_check_deposito = db.Column(db.Boolean, default=False)
    financeiro_check_faturado = db.Column(db.Boolean, default=False)
    financeiro_check_uso_credito = db.Column(db.Boolean, default=False)
    financeiro_check_cortesia = db.Column(db.Boolean, default=False)
    financeiro_check_vendas_online = db.Column(db.Boolean, default=False)
    financeiro_obs = db.Column(db.Text)
    financeiro_user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    financeiro_at = db.Column(db.DateTime)
    diretor_check_dinheiro = db.Column(db.Boolean, default=False)
    diretor_check_cartao = db.Column(db.Boolean, default=False)
    diretor_check_deposito = db.Column(db.Boolean, default=False)
    diretor_check_faturado = db.Column(db.Boolean, default=False)
    diretor_check_uso_credito = db.Column(db.Boolean, default=False)
    diretor_check_cortesia = db.Column(db.Boolean, default=False)
    diretor_check_vendas_online = db.Column(db.Boolean, default=False)
    diretor_obs = db.Column(db.Text)
    diretor_user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    diretor_at = db.Column(db.DateTime)
    cofre_confirmado = db.Column(db.Boolean, default=False)
    cofre_at = db.Column(db.DateTime)
    cofre_obs = db.Column(db.Text)
    status = db.Column(db.String(30), default='aguardando_financeiro')
    financeiro_user = db.relationship('User', foreign_keys=[financeiro_user_id])
    diretor_user = db.relationship('User', foreign_keys=[diretor_user_id])

    def status_label(self):
        labels = {
            'aguardando_financeiro': 'Ag. Financeiro',
            'aguardando_diretor': 'Ag. Diretor',
            'aguardando_cofre': 'Ag. Cofre',
            'concluido': 'Concluido',
        }
        return labels.get(self.status, self.status)

    def tem_divergencia(self):
        return bool(
            (self.financeiro_obs and self.financeiro_obs.strip()) or
            (self.diretor_obs and self.diretor_obs.strip())
        )


class MovimentacaoCofre(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tipo = db.Column(db.String(30), nullable=False)
    descricao = db.Column(db.String(256), nullable=False)
    data = db.Column(db.String(20), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    obs = db.Column(db.Text)
    unidade = db.Column(db.String(120))
    valor = db.Column(db.Float, default=0.0)
    unidade_origem = db.Column(db.String(120))
    unidade_destino = db.Column(db.String(120))
    emprestimo_quitado = db.Column(db.Boolean, default=False)
    emprestimo_quitado_at = db.Column(db.DateTime)
    grupo_id = db.Column(db.String(50))  # agrupa emprestimos do mesmo rateio
    criado_por = db.relationship('User', foreign_keys=[created_by])
    rateios = db.relationship('RateioCofre', backref='movimentacao', lazy=True, cascade='all, delete-orphan')

    def tipo_label(self):
        labels = {
            'saldo_inicial': 'Saldo Inicial',
            'entrada_manual': 'Entrada Manual',
            'saida': 'Saida',
            'saida_rateio': 'Emprestimo Multiplo',
            'emprestimo': 'Emprestimo',
            'devolucao': 'Devolucao',
        }
        return labels.get(self.tipo, self.tipo)


class RateioCofre(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    movimentacao_id = db.Column(db.Integer, db.ForeignKey('movimentacao_cofre.id'), nullable=False)
    unidade = db.Column(db.String(120), nullable=False)
    valor = db.Column(db.Float, default=0.0)


def calcular_saldos():
    saldos = {u: 0.0 for u in UNIDADES_COFRE}
    emprestimos_pendentes = []
    fcs = FechamentoCaixa.query.filter_by(cofre_confirmado=True).all()
    for fc in fcs:
        if fc.unidade in saldos:
            saldos[fc.unidade] += fc.dinheiro_encerramento
    movs = MovimentacaoCofre.query.order_by(MovimentacaoCofre.created_at.asc()).all()
    for mov in movs:
        if mov.tipo == 'saldo_inicial':
            if mov.unidade in saldos:
                saldos[mov.unidade] += mov.valor
        elif mov.tipo == 'entrada_manual':
            if mov.unidade in saldos:
                saldos[mov.unidade] += mov.valor
        elif mov.tipo == 'saida':
            if mov.unidade in saldos:
                saldos[mov.unidade] -= mov.valor
        elif mov.tipo == 'saida_rateio':
            # Debita total da origem — rateios sao emprestimos individuais
            if mov.unidade_origem and mov.unidade_origem in saldos:
                total_rateio = sum(r.valor for r in mov.rateios)
                saldos[mov.unidade_origem] -= total_rateio
            if not mov.emprestimo_quitado:
                emprestimos_pendentes.append(mov)
        elif mov.tipo == 'emprestimo':
            if mov.unidade_origem in saldos:
                saldos[mov.unidade_origem] -= mov.valor
            if not mov.emprestimo_quitado:
                emprestimos_pendentes.append(mov)
        elif mov.tipo == 'devolucao':
            if mov.unidade_origem in saldos:
                saldos[mov.unidade_origem] += mov.valor
    return saldos, emprestimos_pendentes


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/')
@login_required
def index():
    return redirect(url_for('dashboard'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        user = User.query.filter_by(username=username, active=True).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('dashboard'))
        flash('Usuario ou senha invalidos.', 'danger')
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/dashboard')
@login_required
def dashboard():
    fechamentos = FechamentoCaixa.query.all()
    total = len(fechamentos)
    concluidos = sum(1 for f in fechamentos if f.status == 'concluido')
    pendentes = total - concluidos
    unidade_stats = {}
    for u in UNIDADES:
        fcs = [f for f in fechamentos if f.unidade == u]
        total_u = len(fcs)
        concluidos_u = [f for f in fcs if f.status == 'concluido']
        sem_divergencia = sum(1 for f in concluidos_u if not f.tem_divergencia())
        com_divergencia = len(concluidos_u) - sem_divergencia
        unidade_stats[u] = {
            'total': total_u,
            'ok': sem_divergencia,
            'divergencia': com_divergencia,
            'concluidos': len(concluidos_u),
        }
    saldos, emprestimos_pendentes = calcular_saldos()
    total_cofre = sum(v for k, v in saldos.items() if k != 'Leve')
    return render_template('dashboard.html',
                           total=total, concluidos=concluidos, pendentes=pendentes,
                           unidade_stats=unidade_stats, unidades=UNIDADES,
                           saldos=saldos, total_cofre=total_cofre,
                           emprestimos_pendentes=emprestimos_pendentes)


@app.route('/fechamentos')
@login_required
def lista_fechamentos():
    fechamentos = FechamentoCaixa.query.order_by(
        FechamentoCaixa.unidade.asc(),
        FechamentoCaixa.movimento_num.asc()
    ).all()
    return render_template('fechamentos.html', fechamentos=fechamentos, unidades=UNIDADES)


@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    if current_user.role not in ['financeiro', 'admin']:
        flash('Acesso nao autorizado.', 'danger')
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        if 'pdf' not in request.files:
            flash('Nenhum arquivo enviado.', 'danger')
            return redirect(request.url)
        pdf_file = request.files['pdf']
        if pdf_file.filename == '':
            flash('Nenhum arquivo selecionado.', 'danger')
            return redirect(request.url)
        tem_vendas_online = request.form.get('tem_vendas_online') == 'on'
        try:
            vendas_online_valor = float(request.form.get('vendas_online_valor') or 0)
        except ValueError:
            vendas_online_valor = 0.0
        vendas_online_obs = request.form.get('vendas_online_obs', '')
        if pdf_file and pdf_file.filename.lower().endswith('.pdf'):
            filename = secure_filename(datetime.now().strftime('%Y%m%d_%H%M%S') + '_' + pdf_file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            pdf_file.save(filepath)
            try:
                data = extract_caixa_data(filepath)
            except Exception as e:
                flash('Erro ao processar PDF: ' + str(e), 'danger')
                return redirect(request.url)
            fc = FechamentoCaixa(
                unidade=data.get('unidade', ''),
                data_fechamento=data.get('data_fechamento', ''),
                quem_fechou=data.get('quem_fechou', ''),
                movimento_num=data.get('movimento_num', ''),
                pdf_path=filepath,
                dinheiro_saida=data.get('dinheiro_saida', 0),
                dinheiro_encerramento=data.get('dinheiro_encerramento', 0),
                faturado=data.get('faturado', 0),
                uso_credito=data.get('uso_credito', 0),
                deposito_bancario=data.get('deposito_bancario', 0),
                cartao=data.get('cartao', 0),
                cortesia=data.get('cortesia', 0),
                cheque=data.get('cheque', 0),
                cofre_opcional=data.get('cofre_opcional', False),
                tem_vendas_online=tem_vendas_online,
                vendas_online=vendas_online_valor if tem_vendas_online else 0,
                vendas_online_obs=vendas_online_obs if tem_vendas_online else '',
                status='aguardando_financeiro',
            )
            db.session.add(fc)
            db.session.commit()
            flash('PDF processado com sucesso!', 'success')
            return redirect(url_for('fechamento_detail', fc_id=fc.id))
        else:
            flash('Arquivo invalido. Envie apenas .PDF', 'danger')
            return redirect(request.url)
    return render_template('upload.html', unidades=UNIDADES_ATIVAS)


@app.route('/fechamento/<int:fc_id>')
@login_required
def fechamento_detail(fc_id):
    fc = FechamentoCaixa.query.get_or_404(fc_id)
    return render_template('fechamento_detail.html', fc=fc)


@app.route('/fechamento/<int:fc_id>/excluir', methods=['POST'])
@login_required
def excluir_fechamento(fc_id):
    if current_user.role != 'admin':
        return jsonify({'error': 'Nao autorizado'}), 403
    fc = FechamentoCaixa.query.get_or_404(fc_id)
    db.session.delete(fc)
    db.session.commit()
    return jsonify({'success': True})


@app.route('/fechamento/<int:fc_id>/financeiro', methods=['POST'])
@login_required
def financeiro_check(fc_id):
    if current_user.role not in ['financeiro', 'admin']:
        return jsonify({'error': 'Nao autorizado'}), 403
    fc = FechamentoCaixa.query.get_or_404(fc_id)
    data = request.json
    fc.financeiro_check_dinheiro = data.get('check_dinheiro', False)
    fc.financeiro_check_cartao = data.get('check_cartao', False)
    fc.financeiro_check_deposito = data.get('check_deposito', False)
    fc.financeiro_check_faturado = data.get('check_faturado', False)
    fc.financeiro_check_uso_credito = data.get('check_uso_credito', False)
    fc.financeiro_check_cortesia = data.get('check_cortesia', False)
    fc.financeiro_check_vendas_online = data.get('check_vendas_online', False)
    fc.financeiro_obs = data.get('obs', '')
    fc.financeiro_user_id = current_user.id
    fc.financeiro_at = datetime.utcnow()
    fc.status = 'aguardando_diretor'
    db.session.commit()
    return jsonify({'success': True, 'message': 'Conferencia do Financeiro salva!'})


@app.route('/fechamento/<int:fc_id>/diretor', methods=['POST'])
@login_required
def diretor_check(fc_id):
    if current_user.role not in ['diretor', 'admin']:
        return jsonify({'error': 'Nao autorizado'}), 403
    fc = FechamentoCaixa.query.get_or_404(fc_id)
    data = request.json
    fc.diretor_check_dinheiro = data.get('check_dinheiro', False)
    fc.diretor_obs = data.get('obs', '')
    fc.diretor_user_id = current_user.id
    fc.diretor_at = datetime.utcnow()
    enviar_cofre = data.get('enviar_cofre', True)
    if enviar_cofre:
        fc.status = 'aguardando_cofre'
    else:
        fc.cofre_confirmado = False
        fc.status = 'concluido'
    db.session.commit()
    return jsonify({'success': True, 'message': 'Conferencia do Diretor salva!'})


@app.route('/fechamento/<int:fc_id>/cofre', methods=['POST'])
@login_required
def cofre_confirm(fc_id):
    if current_user.role not in ['diretor', 'admin']:
        return jsonify({'error': 'Nao autorizado'}), 403
    fc = FechamentoCaixa.query.get_or_404(fc_id)
    data = request.json
    fc.cofre_confirmado = True
    fc.cofre_at = datetime.utcnow()
    fc.cofre_obs = data.get('obs', '')
    fc.status = 'concluido'
    db.session.commit()
    return jsonify({'success': True, 'message': 'Envio ao cofre registrado!'})


@app.route('/fechamento/<int:fc_id>/relatorio')
@login_required
def gerar_relatorio(fc_id):
    fc = FechamentoCaixa.query.get_or_404(fc_id)
    financeiro_user = User.query.get(fc.financeiro_user_id) if fc.financeiro_user_id else None
    diretor_user = User.query.get(fc.diretor_user_id) if fc.diretor_user_id else None
    try:
        from report_generator import gerar_pdf_relatorio
        pdf_path = gerar_pdf_relatorio(fc, financeiro_user, diretor_user)
        return send_file(pdf_path, as_attachment=True,
                         download_name='relatorio_fechamento_' + str(fc.id) + '.pdf')
    except Exception as e:
        flash('Erro ao gerar relatorio: ' + str(e), 'danger')
        return redirect(url_for('fechamento_detail', fc_id=fc.id))


@app.route('/cofre')
@login_required
def cofre():
    saldos, emprestimos_pendentes = calcular_saldos()
    total_cofre = sum(v for k, v in saldos.items() if k != 'Leve')
    movs = MovimentacaoCofre.query.order_by(MovimentacaoCofre.created_at.desc()).all()
    return render_template('cofre.html',
                           saldos=saldos, total_cofre=total_cofre,
                           emprestimos_pendentes=emprestimos_pendentes,
                           movimentacoes=movs,
                           unidades=UNIDADES_COFRE,
                           unidades_ativas=UNIDADES_ATIVAS + ['Leve'])


@app.route('/cofre/extrato/<unidade>')
@login_required
def extrato_unidade(unidade):
    movs_unidade = []
    if unidade != 'Leve':
        fcs = FechamentoCaixa.query.filter_by(unidade=unidade, cofre_confirmado=True).order_by(FechamentoCaixa.cofre_at.asc()).all()
        for fc in fcs:
            movs_unidade.append({
                'data': fc.cofre_at.strftime('%d/%m/%Y') if fc.cofre_at else fc.data_fechamento,
                'tipo': 'Entrada Caixa',
                'descricao': 'Fechamento Mov. #' + str(fc.movimento_num),
                'entrada': fc.dinheiro_encerramento,
                'saida': 0,
            })
    movs = MovimentacaoCofre.query.order_by(MovimentacaoCofre.created_at.asc()).all()
    for mov in movs:
        if mov.tipo == 'saldo_inicial' and mov.unidade == unidade:
            movs_unidade.append({'data': mov.data, 'tipo': 'Saldo Inicial', 'descricao': mov.descricao, 'entrada': mov.valor, 'saida': 0})
        elif mov.tipo == 'entrada_manual' and mov.unidade == unidade:
            movs_unidade.append({'data': mov.data, 'tipo': 'Entrada Manual', 'descricao': mov.descricao, 'entrada': mov.valor, 'saida': 0})
        elif mov.tipo == 'saida' and mov.unidade == unidade:
            movs_unidade.append({'data': mov.data, 'tipo': 'Saida', 'descricao': mov.descricao, 'entrada': 0, 'saida': mov.valor})
        elif mov.tipo == 'saida_rateio':
            if mov.unidade_origem == unidade:
                total_rateio = sum(r.valor for r in mov.rateios)
                devedores = ' | '.join([r.unidade + ': R$' + '{:,.0f}'.format(r.valor) for r in mov.rateios])
                movs_unidade.append({
                    'data': mov.data,
                    'tipo': 'Emprestimo Multiplo',
                    'descricao': mov.descricao + ' — ' + devedores,
                    'entrada': 0,
                    'saida': total_rateio,
                })
        elif mov.tipo == 'emprestimo':
            if mov.unidade_origem == unidade:
                status_emp = ' (QUITADO)' if mov.emprestimo_quitado else ' (PENDENTE)'
                movs_unidade.append({
                    'data': mov.data,
                    'tipo': 'Emprestimo Concedido',
                    'descricao': 'Para ' + mov.unidade_destino + ': ' + mov.descricao + status_emp,
                    'entrada': 0,
                    'saida': mov.valor,
                })
        elif mov.tipo == 'devolucao':
            if mov.unidade_origem == unidade:
                movs_unidade.append({'data': mov.data, 'tipo': 'Devolucao Recebida', 'descricao': mov.descricao, 'entrada': mov.valor, 'saida': 0})
    saldo_acumulado = 0.0
    for m in movs_unidade:
        saldo_acumulado += m['entrada'] - m['saida']
        m['saldo'] = saldo_acumulado
    saldos, _ = calcular_saldos()
    return render_template('extrato.html', unidade=unidade, movimentacoes=movs_unidade,
                           saldo_atual=saldos.get(unidade, 0), unidades=UNIDADES_COFRE)


@app.route('/cofre/emprestimos')
@login_required
def relatorio_emprestimos():
    data_ini = request.args.get('data_ini', '')
    data_fim = request.args.get('data_fim', '')
    # Busca emprestimos simples
    emprestimos_simples = MovimentacaoCofre.query.filter_by(tipo='emprestimo').order_by(MovimentacaoCofre.created_at.desc()).all()
    # Busca rateios e expande em registros por devedor
    rateios = MovimentacaoCofre.query.filter_by(tipo='saida_rateio').order_by(MovimentacaoCofre.created_at.desc()).all()
    todos = list(emprestimos_simples)
    # Para rateios, cria entrada virtual por devedor
    rateios_expandidos = []
    for r in rateios:
        for rateio in r.rateios:
            rateios_expandidos.append({
                'id': r.id,
                'data': r.data,
                'tipo': 'saida_rateio',
                'unidade_origem': r.unidade_origem,
                'unidade_destino': rateio.unidade,
                'valor': rateio.valor,
                'descricao': r.descricao,
                'emprestimo_quitado': r.emprestimo_quitado,
                'emprestimo_quitado_at': r.emprestimo_quitado_at,
                'grupo_id': r.id,
                'criado_por': r.criado_por,
            })
    if data_ini:
        try:
            dt_ini = datetime.strptime(data_ini, '%Y-%m-%d')
            todos = [e for e in todos if datetime.strptime(e.data, '%d/%m/%Y') >= dt_ini]
            rateios_expandidos = [e for e in rateios_expandidos if datetime.strptime(e['data'], '%d/%m/%Y') >= dt_ini]
        except Exception:
            pass
    if data_fim:
        try:
            dt_fim = datetime.strptime(data_fim, '%Y-%m-%d')
            todos = [e for e in todos if datetime.strptime(e.data, '%d/%m/%Y') <= dt_fim]
            rateios_expandidos = [e for e in rateios_expandidos if datetime.strptime(e['data'], '%d/%m/%Y') <= dt_fim]
        except Exception:
            pass
    total_pendente = (
        sum(e.valor for e in todos if not e.emprestimo_quitado) +
        sum(e['valor'] for e in rateios_expandidos if not e['emprestimo_quitado'])
    )
    total_quitado = (
        sum(e.valor for e in todos if e.emprestimo_quitado) +
        sum(e['valor'] for e in rateios_expandidos if e['emprestimo_quitado'])
    )
    total_geral = total_pendente + total_quitado
    return render_template('relatorio_emprestimos.html',
                           emprestimos=todos,
                           rateios_expandidos=rateios_expandidos,
                           data_ini=data_ini, data_fim=data_fim,
                           total_pendente=total_pendente,
                           total_quitado=total_quitado,
                           total_geral=total_geral)


@app.route('/cofre/emprestimos/pdf')
@login_required
def relatorio_emprestimos_pdf():
    data_ini = request.args.get('data_ini', '')
    data_fim = request.args.get('data_fim', '')
    emprestimos_simples = MovimentacaoCofre.query.filter_by(tipo='emprestimo').order_by(MovimentacaoCofre.created_at.desc()).all()
    rateios = MovimentacaoCofre.query.filter_by(tipo='saida_rateio').order_by(MovimentacaoCofre.created_at.desc()).all()
    todos = list(emprestimos_simples)
    rateios_expandidos = []
    for r in rateios:
        for rateio in r.rateios:
            rateios_expandidos.append({
                'data': r.data, 'unidade_origem': r.unidade_origem,
                'unidade_destino': rateio.unidade, 'valor': rateio.valor,
                'descricao': r.descricao, 'emprestimo_quitado': r.emprestimo_quitado,
            })
    if data_ini:
        try:
            dt_ini = datetime.strptime(data_ini, '%Y-%m-%d')
            todos = [e for e in todos if datetime.strptime(e.data, '%d/%m/%Y') >= dt_ini]
            rateios_expandidos = [e for e in rateios_expandidos if datetime.strptime(e['data'], '%d/%m/%Y') >= dt_ini]
        except Exception:
            pass
    if data_fim:
        try:
            dt_fim = datetime.strptime(data_fim, '%Y-%m-%d')
            todos = [e for e in todos if datetime.strptime(e.data, '%d/%m/%Y') <= dt_fim]
            rateios_expandidos = [e for e in rateios_expandidos if datetime.strptime(e['data'], '%d/%m/%Y') <= dt_fim]
        except Exception:
            pass
    total_pendente = (
        sum(e.valor for e in todos if not e.emprestimo_quitado) +
        sum(e['valor'] for e in rateios_expandidos if not e['emprestimo_quitado'])
    )
    total_quitado = (
        sum(e.valor for e in todos if e.emprestimo_quitado) +
        sum(e['valor'] for e in rateios_expandidos if e['emprestimo_quitado'])
    )
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable
        from reportlab.lib.enums import TA_CENTER
        path = 'relatorios/emprestimos_' + datetime.now().strftime('%Y%m%d%H%M%S') + '.pdf'
        doc = SimpleDocTemplate(path, pagesize=A4,
                                topMargin=1.5*cm, bottomMargin=1.5*cm,
                                leftMargin=2*cm, rightMargin=2*cm)
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle('Title', parent=styles['Title'],
                                     fontSize=16, textColor=colors.HexColor('#1a3a5c'), spaceAfter=6)
        footer_style = ParagraphStyle('Footer', parent=styles['Normal'],
                                      fontSize=8, textColor=colors.grey, alignment=TA_CENTER)
        story = []
        story.append(Paragraph('RELATORIO DE EMPRESTIMOS — OK INN / LEVE HOTEIS', title_style))
        if data_ini and data_fim:
            periodo = 'Periodo: ' + data_ini + ' a ' + data_fim
        elif data_ini:
            periodo = 'A partir de: ' + data_ini
        elif data_fim:
            periodo = 'Ate: ' + data_fim
        else:
            periodo = 'Todos os periodos'
        story.append(Paragraph(periodo, styles['Normal']))
        story.append(Spacer(1, 0.3*cm))
        story.append(HRFlowable(width='100%', thickness=2, color=colors.HexColor('#1a3a5c')))
        story.append(Spacer(1, 0.3*cm))
        dados = [['Data', 'Tipo', 'Origem', 'Devedor', 'Valor', 'Descricao', 'Status']]
        for emp in todos:
            status = 'QUITADO' if emp.emprestimo_quitado else 'PENDENTE'
            dados.append([emp.data, 'Emprestimo', emp.unidade_origem or '-',
                          emp.unidade_destino or '-', 'R$ ' + '{:,.2f}'.format(emp.valor),
                          emp.descricao[:25], status])
        for emp in rateios_expandidos:
            status = 'QUITADO' if emp['emprestimo_quitado'] else 'PENDENTE'
            dados.append([emp['data'], 'Rateio', emp['unidade_origem'] or '-',
                          emp['unidade_destino'] or '-', 'R$ ' + '{:,.2f}'.format(emp['valor']),
                          emp['descricao'][:25], status])
        dados.append(['', '', '', 'Pendente:', 'R$ ' + '{:,.2f}'.format(total_pendente), '', ''])
        dados.append(['', '', '', 'Quitado:', 'R$ ' + '{:,.2f}'.format(total_quitado), '', ''])
        t = Table(dados, colWidths=[1.8*cm, 2*cm, 3*cm, 3*cm, 2.5*cm, 3.2*cm, 2*cm])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a3a5c')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -3), 0.5, colors.lightgrey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -3), [colors.white, colors.HexColor('#f8f9fa')]),
            ('PADDING', (0, 0), (-1, -1), 5),
            ('FONTNAME', (0, -2), (-1, -1), 'Helvetica-Bold'),
        ]))
        story.append(t)
        story.append(Spacer(1, 1*cm))
        story.append(HRFlowable(width='100%', thickness=1, color=colors.lightgrey))
        story.append(Paragraph(
            'Relatorio gerado em ' + datetime.now().strftime('%d/%m/%Y as %H:%M') + ' | Sistema OK INN Leve Hoteis',
            footer_style))
        doc.build(story)
        return send_file(path, as_attachment=True, download_name='relatorio_emprestimos.pdf')
    except Exception as e:
        flash('Erro ao gerar PDF: ' + str(e), 'danger')
        return redirect(url_for('relatorio_emprestimos'))


@app.route('/cofre/movimentacao', methods=['POST'])
@login_required
def nova_movimentacao():
    if current_user.role not in ['diretor', 'admin']:
        return jsonify({'error': 'Nao autorizado'}), 403
    data = request.json
    tipo = data.get('tipo')
    mov = MovimentacaoCofre(
        tipo=tipo,
        descricao=data.get('descricao', ''),
        data=data.get('data', datetime.now().strftime('%d/%m/%Y')),
        created_by=current_user.id,
        obs=data.get('obs', ''),
    )
    if tipo in ['saldo_inicial', 'entrada_manual', 'saida']:
        mov.unidade = data.get('unidade')
        mov.valor = float(data.get('valor', 0))
    elif tipo == 'saida_rateio':
        mov.unidade_origem = data.get('unidade_origem', '')
        rateios = data.get('rateios', [])
        total = sum(float(r.get('valor', 0)) for r in rateios if float(r.get('valor', 0)) > 0)
        mov.valor = total
        for r in rateios:
            if float(r.get('valor', 0)) > 0:
                mov.rateios.append(RateioCofre(unidade=r['unidade'], valor=float(r['valor'])))
    elif tipo == 'emprestimo':
        mov.unidade_origem = data.get('unidade_origem')
        mov.unidade_destino = data.get('unidade_destino')
        mov.valor = float(data.get('valor', 0))
    elif tipo == 'devolucao':
        mov.unidade_origem = data.get('unidade_origem')
        mov.unidade_destino = data.get('unidade_destino')
        mov.valor = float(data.get('valor', 0))
        emp_id = data.get('emprestimo_id')
        if emp_id:
            emp = MovimentacaoCofre.query.get(int(emp_id))
            if emp:
                emp.emprestimo_quitado = True
                emp.emprestimo_quitado_at = datetime.utcnow()
    db.session.add(mov)
    db.session.commit()
    return jsonify({'success': True, 'message': 'Movimentacao registrada!'})


@app.route('/cofre/movimentacao/<int:mov_id>/excluir', methods=['POST'])
@login_required
def excluir_movimentacao(mov_id):
    if current_user.role != 'admin':
        return jsonify({'error': 'Nao autorizado'}), 403
    mov = MovimentacaoCofre.query.get_or_404(mov_id)
    db.session.delete(mov)
    db.session.commit()
    return jsonify({'success': True})


@app.route('/admin/usuarios')
@login_required
def admin_usuarios():
    if current_user.role != 'admin':
        flash('Acesso restrito.', 'danger')
        return redirect(url_for('dashboard'))
    users = User.query.all()
    return render_template('admin_usuarios.html', users=users, roles=ROLES)


@app.route('/admin/usuarios/criar', methods=['POST'])
@login_required
def criar_usuario():
    if current_user.role != 'admin':
        return jsonify({'error': 'Nao autorizado'}), 403
    data = request.json
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'error': 'Usuario ja existe'}), 400
    user = User(username=data['username'], role=data['role'], name=data['name'])
    user.set_password(data['password'])
    db.session.add(user)
    db.session.commit()
    return jsonify({'success': True})


@app.route('/admin/usuarios/<int:user_id>/toggle', methods=['POST'])
@login_required
def toggle_usuario(user_id):
    if current_user.role != 'admin':
        return jsonify({'error': 'Nao autorizado'}), 403
    user = User.query.get_or_404(user_id)
    user.active = not user.active
    db.session.commit()
    return jsonify({'success': True, 'active': user.active})


@app.route('/admin/usuarios/<int:user_id>/senha', methods=['POST'])
@login_required
def alterar_senha(user_id):
    if current_user.role != 'admin' and current_user.id != user_id:
        return jsonify({'error': 'Nao autorizado'}), 403
    user = User.query.get_or_404(user_id)
    data = request.json
    nova_senha = data.get('senha', '')
    if len(nova_senha) < 6:
        return jsonify({'error': 'Senha deve ter pelo menos 6 caracteres'}), 400
    user.set_password(nova_senha)
    db.session.commit()
    return jsonify({'success': True})


@app.route('/minha-senha', methods=['GET', 'POST'])
@login_required
def minha_senha():
    if request.method == 'POST':
        data = request.json
        senha_atual = data.get('senha_atual', '')
        nova_senha = data.get('nova_senha', '')
        if not current_user.check_password(senha_atual):
            return jsonify({'error': 'Senha atual incorreta'}), 400
        if len(nova_senha) < 6:
            return jsonify({'error': 'Nova senha deve ter pelo menos 6 caracteres'}), 400
        current_user.set_password(nova_senha)
        db.session.commit()
        return jsonify({'success': True})
    return render_template('minha_senha.html')

@app.route('/diagnostico/movs')
@login_required
def diagnostico_movs():
    movs = MovimentacaoCofre.query.all()
    resultado = []
    for m in movs:
        resultado.append({
            'id': m.id,
            'tipo': m.tipo,
            'descricao': m.descricao,
            'valor': m.valor,
            'origem': m.unidade_origem,
            'destino': m.unidade_destino,
            'rateios': len(m.rateios),
        })
    return jsonify(resultado)
def init_db():
    with app.app_context():
        db.create_all()
        if not User.query.filter_by(username='admin').first():
            admin = User(username='admin', role='admin', name='Administrador')
            admin.set_password('Admin@2024!')
            db.session.add(admin)
            financeiro = User(username='financeiro', role='financeiro', name='Financeiro')
            financeiro.set_password('Fin@2024!')
            db.session.add(financeiro)
            diretor = User(username='diretor', role='diretor', name='Diretor')
            diretor.set_password('Dir@2024!')
            db.session.add(diretor)
            db.session.commit()


if __name__ == '__main__':
    init_db()
    app.run(debug=True)

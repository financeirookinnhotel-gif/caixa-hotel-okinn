from flask import Flask, render_template, redirect, url_for, flash, request, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
import os
from pdf_extractor import extract_caixa_data

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
database_url = os.environ.get('DATABASE_URL', 'sqlite:///caixa_hotel.db')
if database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql://', 1)
app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
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
    vendas_online = db.Column(db.Float, default=0.0)
    vendas_online_obs = db.Column(db.String(256))
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

    def saude_score(self):
        campos = ['diretor_check_dinheiro', 'diretor_check_cartao',
                  'diretor_check_deposito', 'diretor_check_faturado',
                  'diretor_check_uso_credito', 'diretor_check_cortesia']
        if self.tem_vendas_online:
            campos.append('diretor_check_vendas_online')
        checks = sum(1 for c in campos if getattr(self, c))
        return int((checks / len(campos)) * 100)


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
    criado_por = db.relationship('User', foreign_keys=[created_by])
    rateios = db.relationship('RateioCofre', backref='movimentacao', lazy=True, cascade='all, delete-orphan')

    def tipo_label(self):
        labels = {
            'saldo_inicial': 'Saldo Inicial',
            'entrada_manual': 'Entrada Manual',
            'saida': 'Saida',
            'saida_rateio': 'Saida com Rateio',
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
    saldos = {u: 0.0 for u in UNIDADES}
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
            for rateio in mov.rateios:
                if rateio.unidade in saldos:
                    saldos[rateio.unidade] -= rateio.valor
        elif mov.tipo == 'emprestimo':
            if mov.unidade_origem in saldos:
                saldos[mov.unidade_origem] -= mov.valor
            if mov.unidade_destino in saldos:
                saldos[mov.unidade_destino] += mov.valor
            if not mov.emprestimo_quitado:
                emprestimos_pendentes.append(mov)
        elif mov.tipo == 'devolucao':
            if mov.unidade_origem in saldos:
                saldos[mov.unidade_origem] += mov.valor
            if mov.unidade_destino in saldos:
                saldos[mov.unidade_destino] -= mov.valor
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
        ok = sum(1 for f in fcs if f.status == 'concluido')
        unidade_stats[u] = {'total': len(fcs), 'ok': ok}
    saldos, emprestimos_pendentes = calcular_saldos()
    total_cofre = sum(saldos.values())
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
        tem_vendas_online = request.form.get('tem_vendas_online') == 'on'
        vendas_online_valor = float(request.form.get('vendas_online_valor') or 0)
        vendas_online_obs = request.form.get('vendas_online_obs', '')
        if pdf_file.filename == '':
            flash('Nenhum arquivo selecionado.', 'danger')
            return redirect(request.url)
        if pdf_file and pdf_file.filename.endswith('.pdf'):
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
                tem_vendas_online=tem_vendas_online,
                vendas_online=vendas_online_valor if tem_vendas_online else 0,
                vendas_online_obs=vendas_online_obs if tem_vendas_online else '',
                status='aguardando_financeiro',
            )
            db.session.add(fc)
            db.session.commit()
            flash('PDF processado com sucesso!', 'success')
            return redirect(url_for('fechamento_detail', fc_id=fc.id))
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
    fc.diretor_check_cartao = data.get('check_cartao', False)
    fc.diretor_check_deposito = data.get('check_deposito', False)
    fc.diretor_check_faturado = data.get('check_faturado', False)
    fc.diretor_check_uso_credito = data.get('check_uso_credito', False)
    fc.diretor_check_cortesia = data.get('check_cortesia', False)
    fc.diretor_check_vendas_online = data.get('check_vendas_online', False)
    fc.diretor_obs = data.get('obs', '')
    fc.diretor_user_id = current_user.id
    fc.diretor_at = datetime.utcnow()
    fc.status = 'aguardando_cofre'
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
    total_cofre = sum(saldos.values())
    movs = MovimentacaoCofre.query.order_by(MovimentacaoCofre.created_at.desc()).all()
    return render_template('cofre.html',
                           saldos=saldos, total_cofre=total_cofre,
                           emprestimos_pendentes=emprestimos_pendentes,
                           movimentacoes=movs, unidades=UNIDADES,
                           unidades_ativas=UNIDADES_ATIVAS)


@app.route('/cofre/extrato/<unidade>')
@login_required
def extrato_unidade(unidade):
    movs_unidade = []
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
            for r in mov.rateios:
                if r.unidade == unidade:
                    movs_unidade.append({'data': mov.data, 'tipo': 'Saida Rateio', 'descricao': mov.descricao, 'entrada': 0, 'saida': r.valor})
        elif mov.tipo == 'emprestimo':
            if mov.unidade_origem == unidade:
                movs_unidade.append({'data': mov.data, 'tipo': 'Emprestimo Concedido', 'descricao': 'Para ' + mov.unidade_destino + ': ' + mov.descricao, 'entrada': 0, 'saida': mov.valor})
            elif mov.unidade_destino == unidade:
                movs_unidade.append({'data': mov.data, 'tipo': 'Emprestimo Recebido', 'descricao': 'De ' + mov.unidade_origem + ': ' + mov.descricao, 'entrada': mov.valor, 'saida': 0})
        elif mov.tipo == 'devolucao':
            if mov.unidade_origem == unidade:
                movs_unidade.append({'data': mov.data, 'tipo': 'Devolucao Recebida', 'descricao': mov.descricao, 'entrada': mov.valor, 'saida': 0})
            elif mov.unidade_destino == unidade:
                movs_unidade.append({'data': mov.data, 'tipo': 'Devolucao Realizada', 'descricao': mov.descricao, 'entrada': 0, 'saida': mov.valor})
    saldo_acumulado = 0.0
    for m in movs_unidade:
        saldo_acumulado += m['entrada'] - m['saida']
        m['saldo'] = saldo_acumulado
    saldos, _ = calcular_saldos()
    return render_template('extrato.html', unidade=unidade, movimentacoes=movs_unidade,
                           saldo_atual=saldos.get(unidade, 0), unidades=UNIDADES)


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
        mov.valor = float(data.get('valor_total', 0))
        for r in data.get('rateios', []):
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

@app.route('/diagnostico')
def diagnostico():
    import os
    db_url = os.environ.get('DATABASE_URL', 'sqlite')
    return jsonify({
        'database': db_url[:60],
        'tabelas': db.engine.table_names() if hasattr(db.engine, 'table_names') else 'N/A'
    })
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

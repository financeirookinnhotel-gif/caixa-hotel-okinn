# -*- coding: utf-8 -*-
from flask import Flask, render_template, redirect, url_for, flash, request, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
import os
import json
from pdf_extractor import extract_caixa_data

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///caixa_hotel.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Faca login para acessar o sistema.'

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

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
FECHADORES = ['EDEMILSON', 'ALESSANDRA', 'ERIK', 'DEISE', 'RICHARD']
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
            'aguardando_financeiro': 'Aguardando Financeiro',
            'aguardando_diretor': 'Aguardando Diretor',
            'aguardando_cofre': 'Aguardando Cofre',
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
    fechamentos = FechamentoCaixa.query.order_by(FechamentoCaixa.created_at.desc()).limit(50).all()
    total = FechamentoCaixa.query.count()
    concluidos = FechamentoCaixa.query.filter_by(status='concluido').count()
    pendentes = total - concluidos
    unidade_stats = {}
    for u in UNIDADES:
        total_u = FechamentoCaixa.query.filter_by(unidade=u).count()
        ok_u = FechamentoCaixa.query.filter_by(unidade=u, status='concluido').count()
        unidade_stats[u] = {'total': total_u, 'ok': ok_u}
    return render_template('dashboard.html',
                           fechamentos=fechamentos,
                           total=total,
                           concluidos=concluidos,
                           pendentes=pendentes,
                           unidade_stats=unidade_stats,
                           unidades=UNIDADES)


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
            filename = secure_filename(f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{pdf_file.filename}")
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            pdf_file.save(filepath)
            try:
                data = extract_caixa_data(filepath)
            except Exception as e:
                flash(f'Erro ao processar PDF: {str(e)}', 'danger')
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
    from report_generator import gerar_pdf_relatorio
    fc = FechamentoCaixa.query.get_or_404(fc_id)
    financeiro_user = User.query.get(fc.financeiro_user_id) if fc.financeiro_user_id else None
    diretor_user = User.query.get(fc.diretor_user_id) if fc.diretor_user_id else None
    pdf_path = gerar_pdf_relatorio(fc, financeiro_user, diretor_user)
    return send_file(pdf_path, as_attachment=True,
                     download_name=f'relatorio_fechamento_{fc.id}.pdf')


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


@app.route('/api/stats')
@login_required
def api_stats():
    stats = []
    for u in UNIDADES:
        fcs = FechamentoCaixa.query.filter_by(unidade=u).all()
        total = len(fcs)
        concluidos = sum(1 for f in fcs if f.status == 'concluido')
        pendentes = total - concluidos
        saude = int(sum(f.saude_score() for f in fcs if f.status == 'concluido') / concluidos) if concluidos else 0
        stats.append({'unidade': u, 'total': total, 'concluidos': concluidos,
                      'pendentes': pendentes, 'saude': saude})
    return jsonify(stats)


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

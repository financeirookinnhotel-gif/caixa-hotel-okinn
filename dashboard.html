<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{% block title %}Fechamento de Caixa{% endblock %} | OK INN</title>
  <link href="https://cdnjs.cloudflare.com/ajax/libs/bootstrap/5.3.2/css/bootstrap.min.css" rel="stylesheet">
  <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css" rel="stylesheet">
  <style>
    :root {
      --primary: #1a3a5c;
      --primary-light: #2563a8;
      --accent: #e8a020;
      --success: #198754;
      --danger: #dc3545;
      --bg: #f4f6fb;
    }
    body { background: var(--bg); font-family: 'Segoe UI', sans-serif; }
    .sidebar {
      width: 240px; min-height: 100vh; background: var(--primary);
      position: fixed; top: 0; left: 0; z-index: 100; padding-top: 0;
    }
    .sidebar-brand {
      background: rgba(0,0,0,0.2); padding: 1.2rem 1rem;
      color: white; font-weight: 700; font-size: 1.1rem;
      border-bottom: 1px solid rgba(255,255,255,0.1);
    }
    .sidebar-brand span { color: var(--accent); }
    .sidebar .nav-link {
      color: rgba(255,255,255,0.75); padding: 0.7rem 1.2rem;
      border-radius: 8px; margin: 2px 8px; transition: all 0.2s;
      display: flex; align-items: center; gap: 10px;
    }
    .sidebar .nav-link:hover, .sidebar .nav-link.active {
      color: white; background: rgba(255,255,255,0.15);
    }
    .sidebar .nav-link i { width: 18px; }
    .main-content { margin-left: 240px; padding: 2rem; }
    .topbar {
      background: white; border-bottom: 1px solid #e0e6ef;
      padding: 0.75rem 2rem; margin-left: 240px;
      display: flex; align-items: center; justify-content: space-between;
      position: sticky; top: 0; z-index: 99;
    }
    .topbar-title { font-weight: 600; color: var(--primary); font-size: 1.1rem; }
    .card { border: none; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.07); }
    .card-header { background: var(--primary); color: white; border-radius: 12px 12px 0 0 !important; }
    .badge-status-aguardando_financeiro { background: #ffc107; color: #333; }
    .badge-status-aguardando_diretor { background: #0d6efd; color: white; }
    .badge-status-aguardando_cofre { background: #fd7e14; color: white; }
    .badge-status-concluido { background: #198754; color: white; }
    .check-item {
      display: flex; align-items: center; gap: 12px;
      padding: 10px 14px; border-radius: 8px; margin-bottom: 8px;
      background: white; border: 1px solid #e0e6ef; transition: all 0.2s;
    }
    .check-item:hover { border-color: var(--primary-light); }
    .check-item.checked { border-color: var(--success); background: #f0fff4; }
    .check-item.unchecked { border-color: var(--danger); background: #fff5f5; }
    .check-icon { font-size: 1.2rem; }
    .saude-bar { height: 8px; border-radius: 4px; background: #e0e6ef; overflow: hidden; }
    .saude-fill { height: 100%; border-radius: 4px; transition: width 0.5s; }
    .saude-100 { background: var(--success); }
    .saude-75 { background: #20c997; }
    .saude-50 { background: var(--accent); }
    .saude-25 { background: var(--danger); }
    .btn-primary { background: var(--primary); border-color: var(--primary); }
    .btn-primary:hover { background: var(--primary-light); border-color: var(--primary-light); }
    .stat-card { border-radius: 12px; padding: 1.2rem; color: white; }
    .stat-card.azul { background: linear-gradient(135deg, var(--primary), var(--primary-light)); }
    .stat-card.verde { background: linear-gradient(135deg, #198754, #20c997); }
    .stat-card.laranja { background: linear-gradient(135deg, #fd7e14, #ffc107); color: #333; }
    .stat-card .stat-num { font-size: 2rem; font-weight: 700; }
    .stat-card .stat-label { font-size: 0.85rem; opacity: 0.85; }
    @media (max-width: 768px) {
      .sidebar { transform: translateX(-100%); }
      .main-content, .topbar { margin-left: 0; }
    }
  </style>
  {% block extra_css %}{% endblock %}
</head>
<body>
{% if current_user.is_authenticated %}
<div class="sidebar">
  <div class="sidebar-brand">
    <i class="fas fa-hotel me-2"></i>OK<span>INN</span> Caixas
  </div>
  <nav class="mt-3">
    <a href="{{ url_for('dashboard') }}" class="nav-link {% if request.endpoint == 'dashboard' %}active{% endif %}">
      <i class="fas fa-chart-pie"></i> Dashboard
    </a>
    {% if current_user.role in ['financeiro', 'admin'] %}
    <a href="{{ url_for('upload') }}" class="nav-link {% if request.endpoint == 'upload' %}active{% endif %}">
      <i class="fas fa-upload"></i> Novo Fechamento
    </a>
    {% endif %}
    <a href="{{ url_for('dashboard') }}#fechamentos" class="nav-link">
      <i class="fas fa-list"></i> Fechamentos
    </a>
    {% if current_user.role == 'admin' %}
    <a href="{{ url_for('admin_usuarios') }}" class="nav-link {% if request.endpoint == 'admin_usuarios' %}active{% endif %}">
      <i class="fas fa-users"></i> Usuários
    </a>
    {% endif %}
    <hr style="border-color: rgba(255,255,255,0.15); margin: 1rem 1rem;">
    <a href="{{ url_for('logout') }}" class="nav-link">
      <i class="fas fa-sign-out-alt"></i> Sair
    </a>
  </nav>
  <div style="position: absolute; bottom: 1rem; left: 0; right: 0; padding: 0 1rem;">
    <div style="background: rgba(255,255,255,0.1); border-radius: 8px; padding: 0.6rem 1rem; color: rgba(255,255,255,0.7); font-size: 0.8rem;">
      <i class="fas fa-user-circle me-1"></i>
      <strong>{{ current_user.name }}</strong><br>
      <small>{{ current_user.role.title() }}</small>
    </div>
  </div>
</div>
<div class="topbar">
  <span class="topbar-title">{% block page_title %}{% endblock %}</span>
  <span class="text-muted" style="font-size: 0.85rem;">
    <i class="fas fa-calendar-alt me-1"></i>
    {{ now().strftime('%d/%m/%Y') if now else '' }}
  </span>
</div>
{% endif %}

<div class="{% if current_user.is_authenticated %}main-content{% endif %}">
  {% with messages = get_flashed_messages(with_categories=true) %}
    {% if messages %}
      {% for category, message in messages %}
        <div class="alert alert-{{ category }} alert-dismissible fade show" role="alert">
          {{ message }}
          <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
      {% endfor %}
    {% endif %}
  {% endwith %}
  {% block content %}{% endblock %}
</div>

<script src="https://cdnjs.cloudflare.com/ajax/libs/bootstrap/5.3.2/js/bootstrap.bundle.min.js"></script>
{% block extra_js %}{% endblock %}
</body>
</html>

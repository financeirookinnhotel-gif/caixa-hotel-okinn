{% extends 'base.html' %}
{% block title %}Dashboard{% endblock %}
{% block page_title %}<i class="fas fa-chart-pie me-2"></i>Dashboard de Fechamentos{% endblock %}

{% block content %}
<div class="row g-3 mb-4">
  <div class="col-md-4">
    <div class="stat-card azul">
      <div class="stat-num">{{ total }}</div>
      <div class="stat-label"><i class="fas fa-folder me-1"></i>Total de Fechamentos</div>
    </div>
  </div>
  <div class="col-md-4">
    <div class="stat-card verde">
      <div class="stat-num">{{ concluidos }}</div>
      <div class="stat-label"><i class="fas fa-check-circle me-1"></i>Concluídos</div>
    </div>
  </div>
  <div class="col-md-4">
    <div class="stat-card laranja">
      <div class="stat-num">{{ pendentes }}</div>
      <div class="stat-label"><i class="fas fa-clock me-1"></i>Pendentes</div>
    </div>
  </div>
</div>

<!-- Saúde por unidade -->
<div class="card mb-4">
  <div class="card-header py-3">
    <h6 class="mb-0"><i class="fas fa-heartbeat me-2"></i>Saúde dos Fechamentos por Unidade</h6>
  </div>
  <div class="card-body">
    <div class="row g-3" id="unidade-stats">
      {% for u in unidades %}
      {% set stats = unidade_stats.get(u, {'total': 0, 'ok': 0}) %}
      {% set pct = (stats.ok / stats.total * 100)|int if stats.total > 0 else 0 %}
      {% set ativa = u != 'Floripa Coqueiros' %}
      <div class="col-md-6 col-lg-4">
        <div class="p-3 border rounded-3 bg-white h-100 {{ 'opacity-50' if not ativa }}">
          <div class="d-flex justify-content-between align-items-start mb-2">
            <div>
              <div class="fw-semibold" style="font-size: 0.9rem;">{{ u }}</div>
              <small class="text-muted">{{ stats.total }} fechamentos</small>
            </div>
            {% if not ativa %}
            <span class="badge bg-secondary">Inativo</span>
            {% else %}
            <span class="badge" style="background: {% if pct == 100 %}#198754{% elif pct >= 75 %}#20c997{% elif pct >= 50 %}#ffc107{% else %}#dc3545{% endif %}; color: {% if pct >= 50 and pct < 75 %}#333{% else %}white{% endif %}">
              {{ pct }}%
            </span>
            {% endif %}
          </div>
          {% if ativa %}
          <div class="saude-bar">
            <div class="saude-fill {{ 'saude-100' if pct == 100 else 'saude-75' if pct >= 75 else 'saude-50' if pct >= 50 else 'saude-25' }}"
                 style="width: {{ pct }}%"></div>
          </div>
          <div class="mt-2 d-flex justify-content-between">
            UNIDADES_ATIVAS = [u for u in UNIDADES if u != 'Floripa Coqueiros']
            <small class="text-danger">✗ {{ stats.total - stats.ok }} pendentes</small>
          </div>
          {% endif %}
        </div>
      </div>
      {% endfor %}
    </div>
  </div>
</div>

<!-- Lista de fechamentos -->
<div class="card" id="fechamentos">
  <div class="card-header py-3 d-flex justify-content-between align-items-center">
    <h6 class="mb-0"><i class="fas fa-list me-2"></i>Fechamentos Recentes</h6>
    {% if current_user.role in ['financeiro', 'admin'] %}
    <a href="{{ url_for('upload') }}" class="btn btn-sm btn-light">
      <i class="fas fa-plus me-1"></i>Novo
    </a>
    {% endif %}
  </div>
  <div class="card-body p-0">
    <div class="table-responsive">
      <table class="table table-hover mb-0">
        <thead style="background: #f8f9fa;">
          <tr>
            <th class="px-3 py-2">Unidade</th>
            <th class="py-2">Data</th>
            <th class="py-2">Fechou</th>
            <th class="py-2">Dinheiro Enc.</th>
            <th class="py-2">Cartão</th>
            <th class="py-2">Status</th>
            <th class="py-2">Ações</th>
          </tr>
        </thead>
        <tbody>
          {% for fc in fechamentos %}
          <tr>
            <td class="px-3 py-2 fw-semibold" style="font-size: 0.88rem;">{{ fc.unidade }}</td>
            <td class="py-2 text-muted" style="font-size: 0.88rem;">{{ fc.data_fechamento }}</td>
            <td class="py-2" style="font-size: 0.88rem;">{{ fc.quem_fechou }}</td>
            <td class="py-2" style="font-size: 0.88rem;">
              R$ {{ '%.2f'|format(fc.dinheiro_encerramento)|replace('.', ',') }}
            </td>
            <td class="py-2" style="font-size: 0.88rem;">
              R$ {{ '%.2f'|format(fc.cartao)|replace('.', ',') }}
            </td>
            <td class="py-2">
              <span class="badge badge-status-{{ fc.status }} px-2 py-1" style="font-size: 0.75rem;">
                {{ fc.status_label() }}
              </span>
            </td>
            <td class="py-2">
              <a href="{{ url_for('fechamento_detail', fc_id=fc.id) }}"
                 class="btn btn-sm btn-outline-primary py-0 px-2">
                <i class="fas fa-eye"></i>
              </a>
            </td>
          </tr>
          {% else %}
          <tr>
            <td colspan="7" class="text-center text-muted py-4">
              <i class="fas fa-inbox fa-2x mb-2 d-block"></i>
              Nenhum fechamento registrado ainda.
            </td>
          </tr>
          {% endfor %}
        </tbody>
      </table>
    </div>
  </div>
</div>
{% endblock %}

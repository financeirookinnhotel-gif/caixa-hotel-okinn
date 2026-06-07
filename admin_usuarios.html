{% extends 'base.html' %}
{% block title %}Fechamento #{{ fc.id }}{% endblock %}
{% block page_title %}
  <i class="fas fa-file-invoice me-2"></i>
  Fechamento #{{ fc.id }} — {{ fc.unidade }}
{% endblock %}

{% block extra_css %}
<style>
.check-row {
  display: flex; align-items: center; gap: 12px;
  padding: 12px 16px; border-radius: 10px; margin-bottom: 8px;
  border: 1.5px solid #e0e6ef; background: white; transition: all 0.2s;
}
.check-row.has-check { border-color: #198754; background: #f0fff4; }
.check-row.no-check { border-color: #dc3545; background: #fff5f5; }
.check-row .label { flex: 1; font-weight: 500; }
.check-row .valor { font-size: 1rem; font-weight: 700; color: #1a3a5c; min-width: 130px; text-align: right; }
.custom-check { width: 22px; height: 22px; cursor: pointer; accent-color: #198754; }
.step-badge {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 6px 14px; border-radius: 20px; font-size: 0.82rem; font-weight: 600;
}
.workflow-step {
  display: flex; align-items: center; gap: 8px;
  padding: 10px 16px; border-radius: 10px; margin-bottom: 8px;
  background: #f8f9fa; border: 1.5px solid #e0e6ef;
}
.workflow-step.done { background: #f0fff4; border-color: #198754; }
.workflow-step.current { background: #fff8e1; border-color: #ffc107; }
.workflow-step .step-icon { font-size: 1.3rem; }
.obs-area { border-radius: 8px; border: 1.5px solid #e0e6ef; resize: vertical; min-height: 70px; }
</style>
{% endblock %}

{% block content %}
<div class="row g-4">
  <!-- Coluna esquerda: dados do PDF -->
  <div class="col-lg-5">
    <div class="card mb-4">
      <div class="card-header py-3">
        <h6 class="mb-0"><i class="fas fa-info-circle me-2"></i>Dados do Fechamento</h6>
      </div>
      <div class="card-body">
        <table class="table table-sm table-borderless mb-0">
          <tr><td class="text-muted" style="width:140px">Unidade</td><td class="fw-semibold">{{ fc.unidade }}</td></tr>
          <tr><td class="text-muted">Data Fechamento</td><td>{{ fc.data_fechamento }}</td></tr>
          <tr><td class="text-muted">Fechado por</td><td>{{ fc.quem_fechou }}</td></tr>
          <tr><td class="text-muted">Movimento Nº</td><td>{{ fc.movimento_num }}</td></tr>
          <tr><td class="text-muted">Upload em</td><td>{{ fc.created_at.strftime('%d/%m/%Y %H:%M') }}</td></tr>
          <tr>
            <td class="text-muted">Status</td>
            <td>
              <span class="badge badge-status-{{ fc.status }} px-2 py-1">{{ fc.status_label() }}</span>
            </td>
          </tr>
        </table>
      </div>
    </div>

    <!-- Valores extraídos -->
    <div class="card mb-4">
      <div class="card-header py-3">
        <h6 class="mb-0"><i class="fas fa-coins me-2"></i>Valores Extraídos do PDF</h6>
      </div>
      <div class="card-body pb-2">
        {% set itens = [
          ('4', 'Dinheiro — Saída', fc.dinheiro_saida, 'fas fa-money-bill-alt text-warning'),
          ('5', 'Dinheiro — Encerramento', fc.dinheiro_encerramento, 'fas fa-money-bill text-success'),
          ('6', 'Faturado', fc.faturado, 'fas fa-file-invoice text-primary'),
          ('7', 'Uso de Crédito', fc.uso_credito, 'fas fa-credit-card text-info'),
          ('8', 'Depósito Bancário', fc.deposito_bancario, 'fas fa-university text-secondary'),
          ('9', 'Cartão', fc.cartao, 'fas fa-credit-card text-primary'),
          ('10', 'Cortesia', fc.cortesia, 'fas fa-gift text-danger'),
        ] %}
        {% for num, nome, valor, icon in itens %}
        <div class="d-flex align-items-center gap-2 mb-2 p-2 rounded" style="background:#f8f9fa">
          <span class="badge bg-secondary" style="min-width:26px">{{ num }}</span>
          <i class="{{ icon }}"></i>
          <span class="flex-1" style="font-size:0.9rem">{{ nome }}</span>
          <strong style="color:#1a3a5c">R$ {{ '%.2f'|format(valor) }}</strong>
        </div>
        {% endfor %}
        {% if fc.tem_vendas_online %}
        <div class="d-flex align-items-center gap-2 mb-2 p-2 rounded border border-primary" style="background:#f0f4ff">
          <span class="badge bg-primary" style="min-width:26px"><i class="fas fa-globe"></i></span>
          <i class="fas fa-globe text-primary"></i>
          <span class="flex-1" style="font-size:0.9rem">Vendas Online {{ '(' + fc.vendas_online_obs + ')' if fc.vendas_online_obs else '' }}</span>
          <strong style="color:#1a3a5c">R$ {{ '%.2f'|format(fc.vendas_online) }}</strong>
        </div>
        {% endif %}
      </div>
    </div>

    <!-- Fluxo de status -->
    <div class="card">
      <div class="card-header py-3">
        <h6 class="mb-0"><i class="fas fa-stream me-2"></i>Fluxo de Aprovação</h6>
      </div>
      <div class="card-body">
        <div class="workflow-step {{ 'done' if fc.financeiro_at else 'current' if fc.status == 'aguardando_financeiro' else '' }}">
          <span class="step-icon">{{ '✅' if fc.financeiro_at else '⏳' }}</span>
          <div>
            <div class="fw-semibold">Financeiro</div>
            {% if fc.financeiro_at %}
            <small class="text-muted">
              {{ fc.financeiro_user.name if fc.financeiro_user else '' }} —
              {{ fc.financeiro_at.strftime('%d/%m/%Y %H:%M') }}
            </small>
            {% else %}
            <small class="text-muted">Aguardando conferência</small>
            {% endif %}
          </div>
        </div>
        <div class="workflow-step {{ 'done' if fc.diretor_at else 'current' if fc.status == 'aguardando_diretor' else '' }}">
          <span class="step-icon">{{ '✅' if fc.diretor_at else '⏳' }}</span>
          <div>
            <div class="fw-semibold">Diretor</div>
            {% if fc.diretor_at %}
            <small class="text-muted">
              {{ fc.diretor_user.name if fc.diretor_user else '' }} —
              {{ fc.diretor_at.strftime('%d/%m/%Y %H:%M') }}
            </small>
            {% else %}
            <small class="text-muted">Aguardando conferência</small>
            {% endif %}
          </div>
        </div>
        <div class="workflow-step {{ 'done' if fc.cofre_confirmado else 'current' if fc.status == 'aguardando_cofre' else '' }}">
          <span class="step-icon">{{ '🔒' if fc.cofre_confirmado else '⏳' }}</span>
          <div>
            <div class="fw-semibold">Cofre</div>
            {% if fc.cofre_confirmado %}
            <small class="text-muted">Registrado em {{ fc.cofre_at.strftime('%d/%m/%Y %H:%M') }}</small>
            {% else %}
            <small class="text-muted">Aguardando confirmação do Diretor</small>
            {% endif %}
          </div>
        </div>
        {% if fc.status == 'concluido' %}
        <a href="{{ url_for('gerar_relatorio', fc_id=fc.id) }}" class="btn btn-success w-100 mt-2">
          <i class="fas fa-file-pdf me-2"></i>Baixar Relatório PDF
        </a>
        {% endif %}
      </div>
    </div>
  </div>

  <!-- Coluna direita: conferência -->
  <div class="col-lg-7">

    {% macro check_item(id, label, valor, field_key, checked_fin, checked_dir, can_edit) %}
    <div class="check-row {{ 'has-check' if checked_fin else '' }}" id="row-{{ field_key }}">
      {% if can_edit %}
      <input type="checkbox" class="custom-check check-field" data-field="{{ field_key }}"
             id="chk-{{ field_key }}" {{ 'checked' if checked_fin else '' }}>
      {% else %}
      <span style="font-size:1.2rem">{{ '✅' if checked_fin else '❌' }}</span>
      {% endif %}
      <label class="label" {% if can_edit %}for="chk-{{ field_key }}"{% endif %}>{{ label }}</label>
      <span class="valor">R$ {{ '%.2f'|format(valor) }}</span>
    </div>
    {% endmacro %}

    <!-- FINANCEIRO -->
    {% if current_user.role in ['financeiro', 'admin'] and fc.status == 'aguardando_financeiro' %}
    <div class="card mb-4 border-warning">
      <div class="card-header py-3" style="background:#fff8e1; color:#856404; border-bottom: 1px solid #ffc107;">
        <h6 class="mb-0"><i class="fas fa-check-double me-2"></i>Conferência do Financeiro</h6>
        <small>Marque os itens conferidos. Itens sem check indicam divergência.</small>
      </div>
      <div class="card-body">
        {{ check_item('1', '4 · Dinheiro — Saída', fc.dinheiro_saida, 'dinheiro', fc.financeiro_check_dinheiro, fc.diretor_check_dinheiro, true) }}
        {{ check_item('2', '5 · Dinheiro — Encerramento', fc.dinheiro_encerramento, 'dinheiro_enc', fc.financeiro_check_dinheiro, fc.diretor_check_dinheiro, true) }}
        {{ check_item('3', '9 · Cartão', fc.cartao, 'cartao', fc.financeiro_check_cartao, fc.diretor_check_cartao, true) }}
        {{ check_item('4', '6 · Faturado', fc.faturado, 'faturado', fc.financeiro_check_faturado, fc.diretor_check_faturado, true) }}
        {{ check_item('5', '7 · Uso de Crédito', fc.uso_credito, 'uso_credito', fc.financeiro_check_uso_credito, fc.diretor_check_uso_credito, true) }}
        {{ check_item('6', '8 · Depósito Bancário', fc.deposito_bancario, 'deposito', fc.financeiro_check_deposito, fc.diretor_check_deposito, true) }}
        {{ check_item('7', '10 · Cortesia', fc.cortesia, 'cortesia', fc.financeiro_check_cortesia, fc.diretor_check_cortesia, true) }}
        {% if fc.tem_vendas_online %}
        {{ check_item('8', 'Vendas Online', fc.vendas_online, 'vendas_online', fc.financeiro_check_vendas_online, fc.diretor_check_vendas_online, true) }}
        {% endif %}

        <div class="mt-3">
          <label class="form-label fw-semibold">Observações</label>
          <textarea class="form-control obs-area" id="financeiro-obs" placeholder="Observações sobre divergências...">{{ fc.financeiro_obs or '' }}</textarea>
        </div>
        <button class="btn btn-warning w-100 mt-3 fw-semibold" onclick="salvarFinanceiro()">
          <i class="fas fa-save me-2"></i>Salvar Conferência do Financeiro
        </button>
      </div>
    </div>

    {% elif fc.financeiro_at %}
    <div class="card mb-4 border-success">
      <div class="card-header py-3" style="background:#f0fff4; color:#155724; border-bottom:1px solid #c3e6cb;">
        <h6 class="mb-0"><i class="fas fa-check-circle me-2"></i>Financeiro — Conferido</h6>
        <small>por {{ fc.financeiro_user.name if fc.financeiro_user else '-' }} em {{ fc.financeiro_at.strftime('%d/%m/%Y %H:%M') }}</small>
      </div>
      <div class="card-body">
        {{ check_item('1', '4+5 · Dinheiro', fc.dinheiro_encerramento, 'dinheiro', fc.financeiro_check_dinheiro, false, false) }}
        {{ check_item('2', '9 · Cartão', fc.cartao, 'cartao', fc.financeiro_check_cartao, false, false) }}
        {{ check_item('3', '6 · Faturado', fc.faturado, 'faturado', fc.financeiro_check_faturado, false, false) }}
        {{ check_item('4', '7 · Uso de Crédito', fc.uso_credito, 'uso_credito', fc.financeiro_check_uso_credito, false, false) }}
        {{ check_item('5', '8 · Depósito Bancário', fc.deposito_bancario, 'deposito', fc.financeiro_check_deposito, false, false) }}
        {{ check_item('6', '10 · Cortesia', fc.cortesia, 'cortesia', fc.financeiro_check_cortesia, false, false) }}
        {% if fc.tem_vendas_online %}
        {{ check_item('7', 'Vendas Online', fc.vendas_online, 'vendas_online', fc.financeiro_check_vendas_online, false, false) }}
        {% endif %}
        {% if fc.financeiro_obs %}
        <div class="mt-2 p-2 bg-light rounded"><small><strong>Obs:</strong> {{ fc.financeiro_obs }}</small></div>
        {% endif %}
      </div>
    </div>
    {% endif %}

    <!-- DIRETOR -->
    {% if current_user.role in ['diretor', 'admin'] and fc.status == 'aguardando_diretor' %}
    <div class="card mb-4 border-primary">
      <div class="card-header py-3" style="background:#e8f0fe; color:#1a3a5c; border-bottom:1px solid #b8d0f8;">
        <h6 class="mb-0"><i class="fas fa-user-tie me-2"></i>Conferência do Diretor</h6>
        <small>Confirme os itens após verificar com os dados do Financeiro.</small>
      </div>
      <div class="card-body">
        {% set checks_fin = [fc.financeiro_check_dinheiro, fc.financeiro_check_cartao,
                              fc.financeiro_check_faturado, fc.financeiro_check_uso_credito,
                              fc.financeiro_check_deposito, fc.financeiro_check_cortesia] %}
        <div class="check-row {{ 'has-check' if fc.financeiro_check_dinheiro }}">
          <input type="checkbox" class="custom-check check-dir-field" data-field="dinheiro"
                 id="dir-dinheiro" {{ 'checked' if fc.financeiro_check_dinheiro else '' }}>
          <label class="label" for="dir-dinheiro">4+5 · Dinheiro</label>
          <span class="valor">R$ {{ '%.2f'|format(fc.dinheiro_encerramento) }}</span>
        </div>
        <div class="check-row {{ 'has-check' if fc.financeiro_check_cartao }}">
          <input type="checkbox" class="custom-check check-dir-field" data-field="cartao"
                 id="dir-cartao" {{ 'checked' if fc.financeiro_check_cartao else '' }}>
          <label class="label" for="dir-cartao">9 · Cartão</label>
          <span class="valor">R$ {{ '%.2f'|format(fc.cartao) }}</span>
        </div>
        <div class="check-row {{ 'has-check' if fc.financeiro_check_faturado }}">
          <input type="checkbox" class="custom-check check-dir-field" data-field="faturado"
                 id="dir-faturado" {{ 'checked' if fc.financeiro_check_faturado else '' }}>
          <label class="label" for="dir-faturado">6 · Faturado</label>
          <span class="valor">R$ {{ '%.2f'|format(fc.faturado) }}</span>
        </div>
        <div class="check-row {{ 'has-check' if fc.financeiro_check_uso_credito }}">
          <input type="checkbox" class="custom-check check-dir-field" data-field="uso_credito"
                 id="dir-uso" {{ 'checked' if fc.financeiro_check_uso_credito else '' }}>
          <label class="label" for="dir-uso">7 · Uso de Crédito</label>
          <span class="valor">R$ {{ '%.2f'|format(fc.uso_credito) }}</span>
        </div>
        <div class="check-row {{ 'has-check' if fc.financeiro_check_deposito }}">
          <input type="checkbox" class="custom-check check-dir-field" data-field="deposito"
                 id="dir-dep" {{ 'checked' if fc.financeiro_check_deposito else '' }}>
          <label class="label" for="dir-dep">8 · Depósito Bancário</label>
          <span class="valor">R$ {{ '%.2f'|format(fc.deposito_bancario) }}</span>
        </div>
        <div class="check-row {{ 'has-check' if fc.financeiro_check_cortesia }}">
          <input type="checkbox" class="custom-check check-dir-field" data-field="cortesia"
                 id="dir-cort" {{ 'checked' if fc.financeiro_check_cortesia else '' }}>
          <label class="label" for="dir-cort">10 · Cortesia</label>
          <span class="valor">R$ {{ '%.2f'|format(fc.cortesia) }}</span>
        </div>
        {% if fc.tem_vendas_online %}
        <div class="check-row {{ 'has-check' if fc.financeiro_check_vendas_online }}">
          <input type="checkbox" class="custom-check check-dir-field" data-field="vendas_online"
                 id="dir-vo" {{ 'checked' if fc.financeiro_check_vendas_online else '' }}>
          <label class="label" for="dir-vo">Vendas Online</label>
          <span class="valor">R$ {{ '%.2f'|format(fc.vendas_online) }}</span>
        </div>
        {% endif %}

        <div class="mt-3">
          <label class="form-label fw-semibold">Observações do Diretor</label>
          <textarea class="form-control obs-area" id="diretor-obs" placeholder="Observações...">{{ fc.diretor_obs or '' }}</textarea>
        </div>
        <button class="btn btn-primary w-100 mt-3 fw-semibold" onclick="salvarDiretor()">
          <i class="fas fa-user-check me-2"></i>Salvar Conferência do Diretor
        </button>
      </div>
    </div>
    {% endif %}

    <!-- COFRE -->
    {% if current_user.role in ['diretor', 'admin'] and fc.status == 'aguardando_cofre' %}
    <div class="card mb-4" style="border: 2px solid #fd7e14;">
      <div class="card-header py-3" style="background:#fff3e0; color:#7d3c00; border-bottom:1px solid #fd7e14;">
        <h6 class="mb-0"><i class="fas fa-vault me-2"></i>Registrar Envio ao Cofre</h6>
        <small>Confirme que o dinheiro de R$ {{ '%.2f'|format(fc.dinheiro_encerramento) }} foi enviado ao cofre de {{ fc.unidade }}.</small>
      </div>
      <div class="card-body">
        <div class="alert alert-warning">
          <i class="fas fa-exclamation-triangle me-2"></i>
          <strong>Atenção:</strong> Ao confirmar, será registrado que o valor em dinheiro do fechamento foi enviado ao cofre da unidade.
        </div>
        <div class="mb-3">
          <label class="form-label fw-semibold">Observação (opcional)</label>
          <textarea class="form-control obs-area" id="cofre-obs" placeholder="Ex: Valor conferido e depositado no cofre às 14h..."></textarea>
        </div>
        <button class="btn btn-lg w-100 fw-semibold" style="background:#fd7e14; color:white; border:none;" onclick="confirmarCofre()">
          <i class="fas fa-lock me-2"></i>Confirmar Envio ao Cofre — R$ {{ '%.2f'|format(fc.dinheiro_encerramento) }}
        </button>
      </div>
    </div>
    {% elif fc.cofre_confirmado %}
    <div class="card mb-4 border-success">
      <div class="card-body text-center py-4">
        <i class="fas fa-lock fa-3x text-success mb-2 d-block"></i>
        <h5 class="text-success">Cofre Confirmado</h5>
        <p class="text-muted mb-0">Registrado em {{ fc.cofre_at.strftime('%d/%m/%Y às %H:%M') }}</p>
        {% if fc.cofre_obs %}<small class="text-muted">{{ fc.cofre_obs }}</small>{% endif %}
      </div>
    </div>
    {% endif %}

  </div>
</div>

<div id="toast-container" style="position:fixed; bottom:1.5rem; right:1.5rem; z-index:9999;"></div>
{% endblock %}

{% block extra_js %}
<script>
function showToast(msg, type='success') {
  const c = document.getElementById('toast-container');
  const t = document.createElement('div');
  t.className = `alert alert-${type} py-2 px-3 shadow`;
  t.style.cssText = 'min-width:240px; font-size:0.9rem; border-radius:10px;';
  t.innerHTML = `<i class="fas fa-${type === 'success' ? 'check-circle' : 'exclamation-circle'} me-2"></i>${msg}`;
  c.appendChild(t);
  setTimeout(() => t.remove(), 3500);
}

function getChecks(selector) {
  const checks = {};
  document.querySelectorAll(selector).forEach(el => {
    checks[el.dataset.field] = el.checked;
  });
  return checks;
}

async function salvarFinanceiro() {
  const checks = getChecks('.check-field');
  const obs = document.getElementById('financeiro-obs')?.value || '';
  const body = {
    check_dinheiro: checks['dinheiro'] || checks['dinheiro_enc'] || false,
    check_cartao: checks['cartao'] || false,
    check_faturado: checks['faturado'] || false,
    check_uso_credito: checks['uso_credito'] || false,
    check_deposito: checks['deposito'] || false,
    check_cortesia: checks['cortesia'] || false,
    check_vendas_online: checks['vendas_online'] || false,
    obs,
  };
  const resp = await fetch('/fechamento/{{ fc.id }}/financeiro', {
    method: 'POST', headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(body)
  });
  const data = await resp.json();
  if (data.success) { showToast(data.message); setTimeout(() => location.reload(), 1500); }
  else showToast(data.error || 'Erro', 'danger');
}

async function salvarDiretor() {
  const checks = getChecks('.check-dir-field');
  const obs = document.getElementById('diretor-obs')?.value || '';
  const body = {
    check_dinheiro: checks['dinheiro'] || false,
    check_cartao: checks['cartao'] || false,
    check_faturado: checks['faturado'] || false,
    check_uso_credito: checks['uso_credito'] || false,
    check_deposito: checks['deposito'] || false,
    check_cortesia: checks['cortesia'] || false,
    check_vendas_online: checks['vendas_online'] || false,
    obs,
  };
  const resp = await fetch('/fechamento/{{ fc.id }}/diretor', {
    method: 'POST', headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(body)
  });
  const data = await resp.json();
  if (data.success) { showToast(data.message); setTimeout(() => location.reload(), 1500); }
  else showToast(data.error || 'Erro', 'danger');
}

async function confirmarCofre() {
  const obs = document.getElementById('cofre-obs')?.value || '';
  if (!confirm('Confirmar envio ao cofre?')) return;
  const resp = await fetch('/fechamento/{{ fc.id }}/cofre', {
    method: 'POST', headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({obs})
  });
  const data = await resp.json();
  if (data.success) { showToast('Cofre registrado! Gerando relatório...'); setTimeout(() => location.reload(), 1500); }
  else showToast(data.error || 'Erro', 'danger');
}

// Visual feedback nos checks
document.querySelectorAll('.check-field, .check-dir-field').forEach(el => {
  el.addEventListener('change', function() {
    const row = this.closest('.check-row');
    row.classList.toggle('has-check', this.checked);
    row.classList.toggle('no-check', !this.checked);
  });
});
</script>
{% endblock %}

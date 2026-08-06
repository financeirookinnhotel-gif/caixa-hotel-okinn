{% extends 'base.html' %}
{% block title %}Usuários{% endblock %}
{% block page_title %}<i class="fas fa-users me-2"></i>Gerenciar Usuários{% endblock %}

{% block content %}
<div class="row">
  <div class="col-lg-8">
    <div class="card mb-4">
      <div class="card-header py-3 d-flex justify-content-between align-items-center">
        <h6 class="mb-0">Usuários do Sistema</h6>
        <button class="btn btn-sm btn-light" data-bs-toggle="modal" data-bs-target="#modalNovo">
          <i class="fas fa-plus me-1"></i>Novo Usuário
        </button>
      </div>
      <div class="card-body p-0">
        <table class="table table-hover mb-0">
          <thead style="background:#f8f9fa;">
            <tr>
              <th class="px-3 py-2">Nome</th>
              <th>Usuário</th>
              <th>Perfil</th>
              <th>Status</th>
              <th>Ações</th>
            </tr>
          </thead>
          <tbody>
            {% for u in users %}
            <tr>
              <td class="px-3 py-2 fw-semibold">{{ u.name }}</td>
              <td>{{ u.username }}</td>
              <td>
                <span class="badge {{ 'bg-danger' if u.role == 'admin' else 'bg-primary' if u.role == 'diretor' else 'bg-warning text-dark' }}">
                  {{ u.role.title() }}
                </span>
              </td>
              <td>
                <span class="badge {{ 'bg-success' if u.active else 'bg-secondary' }}">
                  {{ 'Ativo' if u.active else 'Inativo' }}
                </span>
              </td>
              <td>
                {% if u.id != current_user.id %}
                <button class="btn btn-sm btn-outline-{{ 'danger' if u.active else 'success' }} py-0 px-2"
                        onclick="toggleUser({{ u.id }}, this)">
                  <i class="fas fa-{{ 'ban' if u.active else 'check' }}"></i>
                  {{ 'Desativar' if u.active else 'Ativar' }}
                </button>
                {% else %}
                <span class="text-muted" style="font-size:0.8rem">Você</span>
                {% endif %}
              </td>
            </tr>
            {% endfor %}
          </tbody>
        </table>
      </div>
    </div>
  </div>
  <div class="col-lg-4">
    <div class="card">
      <div class="card-header py-3"><h6 class="mb-0">Perfis de Acesso</h6></div>
      <div class="card-body">
        <div class="mb-3">
          <span class="badge bg-warning text-dark mb-1">Financeiro</span>
          <p class="text-muted mb-0" style="font-size:0.85rem">Faz upload do PDF, realiza a primeira conferência dos valores.</p>
        </div>
        <div class="mb-3">
          <span class="badge bg-primary mb-1">Diretor</span>
          <p class="text-muted mb-0" style="font-size:0.85rem">Confirma a conferência e autoriza o envio ao cofre.</p>
        </div>
        <div>
          <span class="badge bg-danger mb-1">Admin</span>
          <p class="text-muted mb-0" style="font-size:0.85rem">Acesso total: gerencia usuários e pode fazer todas as operações.</p>
        </div>
      </div>
    </div>
  </div>
</div>

<!-- Modal Novo Usuário -->
<div class="modal fade" id="modalNovo" tabindex="-1">
  <div class="modal-dialog">
    <div class="modal-content">
      <div class="modal-header" style="background:#1a3a5c; color:white;">
        <h5 class="modal-title"><i class="fas fa-user-plus me-2"></i>Novo Usuário</h5>
        <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
      </div>
      <div class="modal-body">
        <div class="mb-3">
          <label class="form-label fw-semibold">Nome Completo</label>
          <input type="text" id="newName" class="form-control" placeholder="Ex: João Silva">
        </div>
        <div class="mb-3">
          <label class="form-label fw-semibold">Usuário (login)</label>
          <input type="text" id="newUsername" class="form-control" placeholder="Ex: joao.silva">
        </div>
        <div class="mb-3">
          <label class="form-label fw-semibold">Senha</label>
          <input type="password" id="newPassword" class="form-control" placeholder="Mínimo 6 caracteres">
        </div>
        <div class="mb-3">
          <label class="form-label fw-semibold">Perfil</label>
          <select id="newRole" class="form-select">
            <option value="financeiro">Financeiro</option>
            <option value="diretor">Diretor</option>
            <option value="admin">Admin</option>
          </select>
        </div>
      </div>
      <div class="modal-footer">
        <button class="btn btn-secondary" data-bs-dismiss="modal">Cancelar</button>
        <button class="btn btn-primary" onclick="criarUsuario()">
          <i class="fas fa-save me-1"></i>Criar Usuário
        </button>
      </div>
    </div>
  </div>
</div>
{% endblock %}

{% block extra_js %}
<script>
async function criarUsuario() {
  const body = {
    name: document.getElementById('newName').value,
    username: document.getElementById('newUsername').value,
    password: document.getElementById('newPassword').value,
    role: document.getElementById('newRole').value,
  };
  if (!body.name || !body.username || !body.password) {
    alert('Preencha todos os campos!'); return;
  }
  const resp = await fetch('/admin/usuarios/criar', {
    method: 'POST', headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(body)
  });
  const data = await resp.json();
  if (data.success) location.reload();
  else alert(data.error || 'Erro ao criar usuário');
}

async function toggleUser(userId, btn) {
  const resp = await fetch(`/admin/usuarios/${userId}/toggle`, { method: 'POST' });
  const data = await resp.json();
  if (data.success) location.reload();
}
</script>
{% endblock %}

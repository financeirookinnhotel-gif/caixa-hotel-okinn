# 🏨 Sistema de Fechamento de Caixa — OK INN

Sistema web para upload, conferência e aprovação de fechamentos de caixa hoteleiros.

## Funcionalidades

- 📄 Upload e leitura automática de PDFs (sistema HMAX)
- ✅ Fluxo de aprovação: Financeiro → Diretor → Cofre
- 📊 Dashboard com saúde por unidade
- 📑 Geração de relatório PDF ao concluir
- 🌐 Suporte a Vendas Online (segundo PDF do Supervisor)
- 👥 Gestão de usuários com perfis (Financeiro / Diretor / Admin)

## Unidades cadastradas

| Unidade | Status |
|---------|--------|
| Ok Inn Tubarão | ✅ Ativa |
| Ok Inn Express Tubarão | ✅ Ativa |
| Criciúma Express | ✅ Ativa |
| Criciúma Centro | ✅ Ativa |
| Floripa Coqueiros | ⏸️ Inativa (pronta p/ ativar) |
| Atlântico Sul | ✅ Ativa |
| Renascença | ✅ Ativa |
| You HI 01 | ✅ Ativa |

---

## 🚀 Deploy: GitHub + Render

### Passo 1 — Criar repositório no GitHub

1. Acesse [github.com](https://github.com) e faça login
2. Clique em **"New repository"** (botão verde)
3. Nome: `caixa-hotel-okinn`
4. Deixe **Private** (recomendado)
5. **NÃO** marque "Add README" — clique em **Create repository**

### Passo 2 — Subir os arquivos

No terminal do seu computador (ou Git Bash):

```bash
# Entre na pasta do projeto
cd caixa-hotel

# Inicie o Git
git init
git add .
git commit -m "Sistema de fechamento de caixa OK INN"

# Conecte ao GitHub (substitua SEU_USUARIO pelo seu usuário)
git remote add origin https://github.com/financeirookinnhotel-gif/caixa-hotel-okinn.git
git branch -M main
git push -u origin main
```

> 💡 Se pedir senha, use um **Personal Access Token**:
> GitHub → Settings → Developer Settings → Personal Access Tokens → Generate new token (classic) → marque "repo" → gere e use como senha

### Passo 3 — Deploy no Render

1. Acesse [render.com](https://render.com) e faça login
2. Clique em **"New +"** → **"Web Service"**
3. Conecte sua conta GitHub (se ainda não conectou)
4. Selecione o repositório `caixa-hotel-okinn`
5. Configure:
   - **Name:** `caixa-hotel-okinn`
   - **Runtime:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python -c "from app import init_db; init_db()" && gunicorn wsgi:app --bind 0.0.0.0:$PORT`
6. Em **Environment Variables**, adicione:
   - `SECRET_KEY` → clique em "Generate" para gerar automaticamente
7. Clique em **"Create Web Service"**

O Render vai buildar e em ~3 minutos o sistema estará online com uma URL tipo:
`https://caixa-hotel-okinn.onrender.com`

---

## 👤 Usuários padrão (trocar senha após 1º acesso!)

| Usuário | Senha | Perfil |
|---------|-------|--------|
| `admin` | `Admin@2024!` | Admin |
| `financeiro` | `Fin@2024!` | Financeiro |
| `diretor` | `Dir@2024!` | Diretor |

> ⚠️ **Troque as senhas imediatamente** pelo painel de Admin → Usuários

---

## 📋 Como usar

### Financeiro
1. Login com conta Financeiro
2. Menu → **"Novo Fechamento"**
3. Arraste/selecione o PDF do caixa
4. Se houver vendas online, marque a opção e informe o valor
5. Clique em **"Processar PDF"**
6. Na tela do fechamento, confira os valores e marque os ✅
7. Salve a conferência

### Diretor
1. Login com conta Diretor
2. No dashboard, clique no fechamento com status "Aguardando Diretor"
3. Confira os valores e marque os ✅
4. Salve → aparecerá o botão de **Cofre**
5. Confirme o envio ao cofre → relatório PDF é gerado automaticamente

---

## 🔧 Desenvolvimento local

```bash
pip install -r requirements.txt
python wsgi.py
# Acesse: http://localhost:5000
```

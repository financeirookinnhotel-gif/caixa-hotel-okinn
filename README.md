# 🏨 Sistema de Fechamento de Caixa — OK INN / Leve Hotéis

Sistema web para upload, conferência e aprovação de fechamentos de caixa hoteleiros, com gestão de cofre entre unidades.

## Funcionalidades

- 📄 Upload e leitura automática de PDFs (sistema HMAX)
- ✅ Fluxo de aprovação: Financeiro → Diretor → Cofre
- 📊 Dashboard com saúde por unidade e saldo do cofre
- 📑 Geração de relatório PDF ao concluir um fechamento
- 🌐 Suporte a Vendas Online (segundo PDF do Supervisor)
- 🔒 Cofre: saldo por unidade, entradas/saídas manuais, rateio de saída entre unidades
- 🤝 Empréstimos entre unidades (com controle de quitação) e relatório em PDF
- 📜 Extrato de movimentações por unidade
- 👥 Gestão de usuários com perfis (Financeiro / Diretor / Admin)
- 🔑 Troca de senha pelo próprio usuário ("Minha Senha")
- 💾 Exportação de backup completo em JSON (Admin)

## Unidades cadastradas

| Unidade | Status |
|---------|--------|
| Ok Inn Tubarao | ✅ Ativa |
| Ok Inn Express Tubarao | ✅ Ativa |
| Criciuma Express | ✅ Ativa |
| Criciuma Centro | ✅ Ativa |
| Floripa Coqueiros | ⏸️ Inativa (pronta p/ ativar) |
| Atlantico Sul | ✅ Ativa |
| Renascenca | ✅ Ativa |
| You HI 01 | ✅ Ativa |
| Leve | 🔒 Só aparece no Cofre (matriz) |

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
   - **Start Command:** `gunicorn wsgi:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120`
6. Em **Environment Variables**, adicione:
   - `SECRET_KEY` → clique em "Generate" para gerar automaticamente
   - `DATABASE_URL` → se você criar um banco Postgres no Render (recomendado — o disco do Web Service é efêmero e um SQLite local perderia os dados a cada deploy), conecte-o aqui. Sem essa variável, o sistema usa um SQLite local.
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

### Cofre
- Menu **Cofre**: veja o saldo de cada unidade, registre entradas/saídas manuais, saldo inicial, empréstimos entre unidades e saídas com rateio
- **Extrato** por unidade: histórico completo de movimentações e saldo acumulado
- **Relatório de Empréstimos**: lista empréstimos pendentes/quitados, com filtro por período e exportação em PDF

---

## 🔧 Desenvolvimento local

O `wsgi.py` não sobe servidor sozinho (ele é feito para rodar via `gunicorn`, que não funciona nativamente no Windows). Para testar localmente:

```bash
pip install -r requirements.txt
python -c "from wsgi import app; app.run(debug=True)"
# Acesse: http://localhost:5000
```

Em Linux/Mac, você também pode usar o gunicorn diretamente:

```bash
gunicorn wsgi:app --bind 0.0.0.0:5000
```

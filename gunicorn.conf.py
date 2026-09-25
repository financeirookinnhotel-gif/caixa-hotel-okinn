import os

# O gunicorn carrega este arquivo automaticamente por estar na raiz do
# projeto, independente de qual Start Command o Render estiver usando
# (Procfile, render.yaml ou um comando configurado manualmente no
# painel). Processar um PDF do HITS mais pesado pode levar mais de 30s
# no CPU do Render, entao o timeout precisa ficar bem acima disso.
timeout = int(os.environ.get('GUNICORN_TIMEOUT', '180'))
workers = int(os.environ.get('WEB_CONCURRENCY', '1'))
bind = '0.0.0.0:' + os.environ.get('PORT', '10000')

from datetime import datetime
from app import app, db, init_db
import os

@app.context_processor
def inject_now():
    return {'now': datetime.now}

with app.app_context():
    try:
        db.create_all()
        init_db()
        print('Banco de dados inicializado com sucesso!')
        print('DATABASE_URL:', os.environ.get('DATABASE_URL', 'sqlite (padrao)')[:50])
    except Exception as e:
        print('ERRO ao inicializar banco:', str(e))

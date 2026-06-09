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
        # Adiciona colunas novas se nao existirem no PostgreSQL
        with db.engine.connect() as conn:
            try:
                conn.execute(db.text('ALTER TABLE fechamento_caixa ADD COLUMN cheque FLOAT DEFAULT 0.0'))
                conn.commit()
                print('Coluna cheque adicionada')
            except Exception:
                pass
            try:
                conn.execute(db.text('ALTER TABLE fechamento_caixa ADD COLUMN cofre_opcional BOOLEAN DEFAULT FALSE'))
                conn.commit()
                print('Coluna cofre_opcional adicionada')
            except Exception:
                pass
        print('Banco inicializado!')
    except Exception as e:
        print('ERRO:', str(e))
